"""CBC-based CVRP solver with Branch-and-Bound trajectory logging.

Wraps the MILP builder, solves with PuLP's CBC interface, parses the
solver log for incumbent/bound trajectories, and decodes the solution.
"""

from __future__ import annotations

import re
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pulp

from .decode import decode_solution
from .feasibility import check_feasibility
from .milp import build_cvrp_model
from .models import Instance, Solution


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TrajectoryPoint:
    """A single observation from the B&B search.

    Attributes:
        time_s: Wall-clock seconds since solve start.
        incumbent: Best known objective, or *None* if no integer
            solution has been found yet.
        best_bound: Best possible (lower) bound, or *None* if unknown.
        nodes: B&B node count at this point, or *None*.
    """

    time_s: float
    incumbent: float | None
    best_bound: float | None
    nodes: int | None


@dataclass(frozen=True)
class SolveResult:
    """Complete result of solving a CVRP instance with CBC.

    Attributes:
        instance_name: Name of the instance that was solved.
        n_customers: Number of customers.
        status: PuLP status string (e.g. "Optimal", "Not Solved").
        best_objective: Best integer objective found, or *None*.
        lp_relaxation_bound: LP relaxation objective, or *None*.
        best_bound: Best possible bound at termination, or *None*.
        mip_gap: Relative MIP gap, or *None*.
        n_nodes: Total B&B nodes explored, or *None*.
        wall_time_s: Total wall-clock solve time in seconds.
        feasible: Whether the decoded solution passes feasibility.
        solution: Decoded :class:`Solution`, or *None* if no incumbent.
        trajectory: Tuple of trajectory observations.
    """

    instance_name: str
    n_customers: int
    status: str
    best_objective: float | None
    lp_relaxation_bound: float | None
    best_bound: float | None
    mip_gap: float | None
    n_nodes: int | None
    wall_time_s: float
    feasible: bool
    solution: Solution | None
    trajectory: tuple[TrajectoryPoint, ...]


# ---------------------------------------------------------------------------
# CBC log parsing
# ---------------------------------------------------------------------------

# Sentinel value CBC uses for "no integer solution yet".
_NO_SOLUTION_SENTINEL = 1e+49  # anything >= this is treated as None

# Progress line: After N nodes, M on tree, INC best solution, best possible BOUND (T seconds)
_RE_PROGRESS = re.compile(
    r"Cbc0010I After (\d+) nodes?, .+?, "
    r"([\d.e+]+) best solution, best possible ([\d.e+-]+) "
    r"\(([\d.]+) seconds\)"
)

# New integer solution found (various methods).
_RE_INTEGER_SOL = re.compile(
    r"Cbc00(?:04|12|16)I Integer solution of ([\d.e+-]+) "
    r"found .+?(\d+) nodes? \(([\d.]+) seconds\)"
)

# Search completed line.
_RE_COMPLETED = re.compile(
    r"Cbc0001I Search completed - best objective ([\d.e+-]+).*?"
    r"(\d+) nodes? \(([\d.]+) seconds\)"
)

# Partial search (time limit hit).
_RE_PARTIAL = re.compile(
    r"Cbc0005I Partial search - best objective ([\d.e+-]+) "
    r"\(best possible ([\d.e+-]+)\).*?(\d+) nodes? \(([\d.]+) seconds\)"
)


@dataclass(frozen=True)
class _LogSummary:
    """Parsed summary from a CBC solve log."""

    trajectory: list[TrajectoryPoint]
    final_nodes: int | None
    final_best_bound: float | None


# Summary section: "Lower bound:  <VAL>"
_RE_LOWER_BOUND = re.compile(r"Lower bound:\s+([\d.e+-]+)")

# Summary section: "Enumerated nodes:  <N>"
_RE_ENUM_NODES = re.compile(r"Enumerated nodes:\s+(\d+)")


def _parse_cbc_log(log_text: str) -> _LogSummary:
    """Parse a CBC log for trajectory points and summary stats.

    Returns:
        A :class:`_LogSummary` with trajectory, node count, and
        the final best bound from the log summary section.
    """
    points: list[TrajectoryPoint] = []
    final_nodes: int | None = None
    final_best_bound: float | None = None

    for line in log_text.splitlines():
        m = _RE_PROGRESS.search(line)
        if m:
            nodes = int(m.group(1))
            inc_val = float(m.group(2))
            bound_val = float(m.group(3))
            secs = float(m.group(4))
            inc = None if inc_val >= _NO_SOLUTION_SENTINEL else inc_val
            points.append(TrajectoryPoint(
                time_s=secs, incumbent=inc,
                best_bound=bound_val, nodes=nodes,
            ))
            final_nodes = nodes
            continue

        m = _RE_INTEGER_SOL.search(line)
        if m:
            val = float(m.group(1))
            nodes = int(m.group(2))
            secs = float(m.group(3))
            if val < _NO_SOLUTION_SENTINEL:
                points.append(TrajectoryPoint(
                    time_s=secs, incumbent=val,
                    best_bound=None, nodes=nodes,
                ))
            final_nodes = max(final_nodes or 0, nodes)
            continue

        m = _RE_COMPLETED.search(line)
        if m:
            final_nodes = int(m.group(2))
            continue

        m = _RE_PARTIAL.search(line)
        if m:
            final_best_bound = float(m.group(2))
            final_nodes = int(m.group(3))
            continue

        m = _RE_LOWER_BOUND.search(line)
        if m:
            final_best_bound = float(m.group(1))
            continue

        m = _RE_ENUM_NODES.search(line)
        if m:
            final_nodes = int(m.group(1))

    return _LogSummary(
        trajectory=points,
        final_nodes=final_nodes,
        final_best_bound=final_best_bound,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def solve_cvrp(
    instance: Instance,
    *,
    time_limit: int,
    round_distances: bool = False,
    msg: bool = False,
) -> SolveResult:
    """Solve a CVRP instance with CBC and return a detailed result.

    Args:
        instance: The CVRP instance to solve.
        time_limit: Maximum solve time in seconds.
        round_distances: Round Euclidean distances to integers.
        msg: If *True*, print CBC output to stdout.

    Returns:
        A :class:`SolveResult` with trajectory, decoded solution, and
        feasibility status.
    """
    model, variables = build_cvrp_model(instance, round_distances=round_distances)
    x_vars: dict[tuple[int, int], pulp.LpVariable] = variables["x"]

    # Solve with CBC, logging to a temp file for parsing.
    log_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False,
    )
    log_path = log_file.name
    log_file.close()

    solver = pulp.PULP_CBC_CMD(
        timeLimit=time_limit, threads=1, msg=msg, logPath=log_path,
    )

    t0 = time.perf_counter()
    model.solve(solver)
    wall_time = time.perf_counter() - t0

    # Parse the CBC log.
    log_text = Path(log_path).read_text()
    Path(log_path).unlink(missing_ok=True)

    log_summary = _parse_cbc_log(log_text)
    trajectory_points = log_summary.trajectory
    parsed_nodes = log_summary.final_nodes

    # Extract status and objective.
    status = pulp.LpStatus[model.status]
    obj_value = pulp.value(model.objective)
    best_objective: float | None = None
    if obj_value is not None and model.status == 1:
        best_objective = float(obj_value)

    # Compute LP relaxation bound.
    lp_bound = lp_relaxation_bound(instance, round_distances=round_distances)

    # Best bound: prefer the log summary (most accurate), fall back to
    # the last trajectory point that has one.
    best_bound = log_summary.final_best_bound
    if best_bound is None:
        for pt in reversed(trajectory_points):
            if pt.best_bound is not None:
                best_bound = pt.best_bound
                break
    # For proven-optimal solutions, best_bound == best_objective.
    if best_bound is None and best_objective is not None and status == "Optimal":
        best_bound = best_objective

    # MIP gap.
    mip_gap: float | None = None
    if best_objective is not None and best_bound is not None:
        denom = max(abs(best_objective), 1e-9)
        mip_gap = abs(best_objective - best_bound) / denom

    # Decode solution.
    solution: Solution | None = None
    feasible = False
    if best_objective is not None:
        x_values: dict[tuple[int, int], float] = {
            arc: var.varValue if var.varValue is not None else 0.0
            for arc, var in x_vars.items()
        }
        solution = decode_solution(
            instance, x_values, round_distances=round_distances,
        )
        report = check_feasibility(instance, solution)
        feasible = report.feasible

    return SolveResult(
        instance_name=instance.name,
        n_customers=instance.n_customers,
        status=status,
        best_objective=best_objective,
        lp_relaxation_bound=lp_bound,
        best_bound=best_bound,
        mip_gap=mip_gap,
        n_nodes=parsed_nodes,
        wall_time_s=wall_time,
        feasible=feasible,
        solution=solution,
        trajectory=tuple(trajectory_points),
    )


def lp_relaxation_bound(
    instance: Instance,
    *,
    round_distances: bool = False,
) -> float:
    """Compute the LP relaxation bound for a CVRP instance.

    Rebuilds the MILP with all binary variables relaxed to continuous
    [0, 1] and solves with CBC.

    Args:
        instance: The CVRP instance.
        round_distances: Round distances to integers.

    Returns:
        The LP relaxation objective value.
    """
    model, variables = build_cvrp_model(instance, round_distances=round_distances)
    x_vars: dict[tuple[int, int], Any] = variables["x"]

    # Relax all binary x variables to continuous.
    for var in x_vars.values():
        var.cat = pulp.const.LpContinuous

    solver = pulp.PULP_CBC_CMD(msg=False, threads=1)
    model.solve(solver)

    obj = pulp.value(model.objective)
    assert obj is not None, "LP relaxation must be feasible"
    return float(obj)