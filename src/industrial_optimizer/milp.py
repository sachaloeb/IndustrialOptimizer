"""MILP builder for the Capacitated Vehicle Routing Problem.

Uses a two-index formulation with Miller-Tucker-Zemlin (MTZ) subtour
elimination.  The model is *built* but **not solved** -- solving is
deferred to the benchmark runner (Weeks 3-4).

Formulation
-----------
Sets
    N = {0} U C   (depot plus customers)
    C             (customers only)

Parameters
    c[i,j]  Euclidean distance between nodes i and j
    d[i]    demand of customer i
    Q       vehicle capacity
    K       fleet size

Variables
    x[i,j] in {0,1}       for all (i,j) in N x N, i != j
    u[i]   in [d[i], Q]   for all i in C

Objective
    minimise  sum_{(i,j)} c[i,j] * x[i,j]

Constraints
    (1) sum_j x[i,j]  = 1          for all i in C   (leave each customer once)
    (2) sum_i x[i,j]  = 1          for all j in C   (enter each customer once)
    (3) sum_j x[0,j] <= K                            (depot out-degree)
    (4) sum_i x[i,0] <= K                            (depot in-degree)
    (5) u[j] >= u[i] + d[j] - Q*(1-x[i,j])          for all i,j in C, i!=j  (MTZ)
    (6) d[i] <= u[i] <= Q                            (encoded as variable bounds)
"""

from typing import Any

import pulp

from .models import Instance, compute_distance_matrix


def build_cvrp_model(
    instance: Instance,
    *,
    round_distances: bool = False,
) -> tuple[pulp.LpProblem, dict[str, Any]]:
    """Build (but do not solve) a CVRP MILP model.

    Args:
        instance: The CVRP instance to model.
        round_distances: If *True*, round Euclidean distances to the
            nearest integer (useful for CVRPLIB compatibility).

    Returns:
        A ``(model, vars)`` tuple where *vars* is a dict with keys:

        - ``"x"``: ``dict[(i, j), LpVariable]`` -- arc variables.
        - ``"u"``: ``dict[i, LpVariable]`` -- accumulated-load variables.
    """
    nodes = instance.all_nodes
    depot_id = instance.depot.id
    customer_ids = [c.id for c in instance.customers]
    all_ids = [n.id for n in nodes]
    demand = {c.id: c.demand for c in instance.customers}
    fleet_size = instance.n_vehicles
    capacity = instance.capacity

    dist = compute_distance_matrix(nodes, round_distances=round_distances)

    model = pulp.LpProblem("CVRP", pulp.LpMinimize)

    # ---- Decision variables ------------------------------------------------
    x: dict[tuple[int, int], pulp.LpVariable] = {}
    for i in all_ids:
        for j in all_ids:
            if i != j:
                x[i, j] = pulp.LpVariable(f"x_{i}_{j}", cat=pulp.const.LpBinary)

    u: dict[int, pulp.LpVariable] = {}
    for i in customer_ids:
        u[i] = pulp.LpVariable(
            f"u_{i}",
            lowBound=demand[i],
            upBound=capacity,
            cat=pulp.const.LpContinuous,
        )

    # ---- Objective ---------------------------------------------------------
    model += (
        pulp.lpSum(dist[i, j] * x[i, j] for (i, j) in x),
        "total_distance",
    )

    # ---- Constraints -------------------------------------------------------
    # (1) Each customer is left exactly once.
    for i in customer_ids:
        model += (
            pulp.lpSum(x[i, j] for j in all_ids if j != i) == 1,
            f"leave_{i}",
        )

    # (2) Each customer is entered exactly once.
    for j in customer_ids:
        model += (
            pulp.lpSum(x[i, j] for i in all_ids if i != j) == 1,
            f"enter_{j}",
        )

    # (3) Depot out-degree bounded by fleet size.
    model += (
        pulp.lpSum(x[depot_id, j] for j in all_ids if j != depot_id) <= fleet_size,
        "depot_out",
    )

    # (4) Depot in-degree bounded by fleet size.
    model += (
        pulp.lpSum(x[i, depot_id] for i in all_ids if i != depot_id) <= fleet_size,
        "depot_in",
    )

    # (5) MTZ subtour elimination / capacity coupling.
    for i in customer_ids:
        for j in customer_ids:
            if i != j:
                model += (
                    u[j] >= u[i] + demand[j] - capacity * (1 - x[i, j]),
                    f"mtz_{i}_{j}",
                )

    variables: dict[str, Any] = {"x": x, "u": u}
    return model, variables