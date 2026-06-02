#!/usr/bin/env python3
"""Benchmark runner for CVRP solvers.

Sweeps instance sizes × seeds × time budgets, writes results to CSV,
trajectory data per run, and a run-metadata JSON file.

Usage::

    python bench/run_benchmark.py               # full sweep
    python bench/run_benchmark.py --quick        # fast smoke-test
    python bench/run_benchmark.py --out results  # custom output dir
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import pulp

# Ensure the package is importable when running from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from industrial_optimizer.generator import generate_instance  # noqa: E402
from industrial_optimizer.solver import SolveResult, solve_cvrp  # noqa: E402

# ---------------------------------------------------------------------------
# Tier definitions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Tier:
    """A size tier for the benchmark sweep."""

    name: str
    n_customers: int
    capacity: int
    n_vehicles: int


DEFAULT_TIERS: tuple[Tier, ...] = (
    Tier(name="small", n_customers=10, capacity=50, n_vehicles=10),
    Tier(name="medium", n_customers=20, capacity=50, n_vehicles=20),
    Tier(name="large", n_customers=35, capacity=50, n_vehicles=35),
)

QUICK_TIERS: tuple[Tier, ...] = (DEFAULT_TIERS[0],)

DEFAULT_SEEDS = (0, 1, 2, 3, 4)
QUICK_SEEDS = (0, 1)

DEFAULT_BUDGETS = (1, 10, 60)
QUICK_BUDGETS = (1,)

CSV_HEADER = (
    "method",
    "instance_name",
    "tier",
    "n_customers",
    "seed",
    "time_budget_s",
    "status",
    "best_objective",
    "lp_relaxation_bound",
    "best_bound",
    "mip_gap",
    "n_nodes",
    "wall_time_s",
    "feasible",
)

TRAJECTORY_HEADER = ("time_s", "incumbent", "best_bound", "nodes")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt(val: object) -> str:
    """Format a value for CSV output (None -> empty string)."""
    if val is None:
        return ""
    if isinstance(val, float):
        return f"{val:.8g}"
    if isinstance(val, bool):
        return str(val)
    return str(val)


def _write_trajectory(
    result: SolveResult,
    path: Path,
) -> None:
    """Write a trajectory CSV for one solve run."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(TRAJECTORY_HEADER)
        for pt in result.trajectory:
            writer.writerow([
                f"{pt.time_s:.4f}",
                _fmt(pt.incumbent),
                _fmt(pt.best_bound),
                _fmt(pt.nodes),
            ])


def _write_meta(
    out_dir: Path,
    tiers: Sequence[Tier],
    seeds: Sequence[int],
    budgets: Sequence[int],
) -> None:
    """Write run_meta.json with environment and config info."""
    cbc_version = "unknown"
    try:
        cbc_version = pulp.PULP_CBC_CMD().actualSolve.__func__.__qualname__  # type: ignore[attr-defined]
    except Exception:
        pass
    # Try to get CBC version from the solver path.
    try:
        solver = pulp.PULP_CBC_CMD()
        cbc_version = str(solver.path)
    except Exception:
        pass

    meta = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "pulp_version": pulp.__version__,
        "cbc_path": str(pulp.PULP_CBC_CMD().path),
        "platform": platform.platform(),
        "tiers": [
            {"name": t.name, "n_customers": t.n_customers,
             "capacity": t.capacity, "n_vehicles": t.n_vehicles}
            for t in tiers
        ],
        "seeds": list(seeds),
        "budgets_s": list(budgets),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    meta_path = out_dir / "run_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Main sweep
# ---------------------------------------------------------------------------

def run_sweep(
    *,
    tiers: Sequence[Tier],
    seeds: Sequence[int],
    budgets: Sequence[int],
    out_dir: Path,
    method: str = "milp",
) -> Path:
    """Execute the benchmark sweep and return the path to results.csv."""
    results_dir = out_dir
    results_dir.mkdir(parents=True, exist_ok=True)
    traj_dir = out_dir / "trajectories"
    traj_dir.mkdir(parents=True, exist_ok=True)

    csv_path = results_dir / "results.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)

        total_runs = len(tiers) * len(seeds) * len(budgets)
        run_idx = 0

        for tier in tiers:
            for seed in seeds:
                inst = generate_instance(
                    n_customers=tier.n_customers,
                    grid_size=100,
                    demand_low=1,
                    demand_high=10,
                    capacity=tier.capacity,
                    n_vehicles=tier.n_vehicles,
                    seed=seed,
                )
                for budget in budgets:
                    run_idx += 1
                    print(
                        f"[{run_idx}/{total_runs}] {tier.name} "
                        f"n={tier.n_customers} seed={seed} "
                        f"budget={budget}s ...",
                        end="",
                        flush=True,
                    )

                    result = solve_cvrp(
                        inst, time_limit=budget, round_distances=False,
                    )

                    row = [
                        method,
                        result.instance_name,
                        tier.name,
                        result.n_customers,
                        seed,
                        budget,
                        result.status,
                        _fmt(result.best_objective),
                        _fmt(result.lp_relaxation_bound),
                        _fmt(result.best_bound),
                        _fmt(result.mip_gap),
                        _fmt(result.n_nodes),
                        f"{result.wall_time_s:.4f}",
                        result.feasible,
                    ]
                    writer.writerow(row)
                    f.flush()

                    # Write trajectory.
                    traj_name = f"{inst.name}__{budget}s.csv"
                    _write_trajectory(result, traj_dir / traj_name)

                    status_str = result.status
                    obj_str = (
                        f"{result.best_objective:.2f}"
                        if result.best_objective is not None
                        else "N/A"
                    )
                    print(
                        f" {status_str} obj={obj_str} "
                        f"t={result.wall_time_s:.1f}s"
                    )

    _write_meta(results_dir, tiers, seeds, budgets)
    return csv_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CVRP benchmark sweep (MILP/CBC).",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run a minimal sweep for testing/dev.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "results",
        help="Output directory (default: bench/results).",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=None,
        help="Override seed list.",
    )
    parser.add_argument(
        "--budgets",
        type=int,
        nargs="+",
        default=None,
        help="Override time-budget list (seconds).",
    )
    parser.add_argument(
        "--tiers",
        type=str,
        nargs="+",
        choices=["small", "medium", "large"],
        default=None,
        help="Override tier selection.",
    )

    args = parser.parse_args(argv)

    if args.quick:
        tiers = QUICK_TIERS
        seeds = QUICK_SEEDS
        budgets = QUICK_BUDGETS
    else:
        tiers = DEFAULT_TIERS
        seeds = DEFAULT_SEEDS
        budgets = DEFAULT_BUDGETS

    if args.seeds is not None:
        seeds = tuple(args.seeds)
    if args.budgets is not None:
        budgets = tuple(args.budgets)
    if args.tiers is not None:
        tier_map = {t.name: t for t in DEFAULT_TIERS}
        tiers = tuple(tier_map[n] for n in args.tiers)

    csv_path = run_sweep(
        tiers=tiers,
        seeds=seeds,
        budgets=budgets,
        out_dir=args.out,
    )
    print(f"\nResults written to {csv_path}")


if __name__ == "__main__":
    main()