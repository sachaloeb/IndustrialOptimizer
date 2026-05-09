"""Solver-independent feasibility checker for CVRP solutions.

Validates a :class:`Solution` against an :class:`Instance` and returns a
:class:`FeasibilityReport` listing every violation found.

Checked constraints
-------------------
1. Every customer is visited exactly once across all routes.
2. No route exceeds the vehicle capacity.
3. Every route starts and ends at the depot.
4. The number of routes does not exceed the fleet size.
"""

from models import FeasibilityReport, Instance, Solution


def check_feasibility(instance: Instance, solution: Solution) -> FeasibilityReport:
    """Check whether *solution* is feasible for *instance*.

    Args:
        instance: The CVRP instance.
        solution: The candidate solution.

    Returns:
        A :class:`FeasibilityReport` with ``feasible=True`` iff no
        violations were detected.
    """
    violations: list[str] = []
    depot_id = instance.depot.id
    customer_ids = {c.id for c in instance.customers}
    demand_map = {c.id: c.demand for c in instance.customers}

    # --- 1. Customer coverage -----------------------------------------------
    visited: set[int] = set()
    for route in solution.routes:
        for nid in route.node_ids:
            if nid in customer_ids:
                if nid in visited:
                    violations.append(
                        f"Customer {nid} visited more than once"
                    )
                visited.add(nid)

    unvisited = customer_ids - visited
    if unvisited:
        violations.append(f"Unvisited customers: {sorted(unvisited)}")

    # --- 2. Capacity --------------------------------------------------------
    for route in solution.routes:
        load = sum(demand_map.get(nid, 0) for nid in route.node_ids)
        if load > instance.capacity:
            violations.append(
                f"Route for vehicle {route.vehicle_id} exceeds capacity: "
                f"{load} > {instance.capacity}"
            )

    # --- 3. Depot closure ---------------------------------------------------
    for route in solution.routes:
        if not route.node_ids or route.node_ids[0] != depot_id:
            violations.append(
                f"Route for vehicle {route.vehicle_id} does not start at depot"
            )
        if not route.node_ids or route.node_ids[-1] != depot_id:
            violations.append(
                f"Route for vehicle {route.vehicle_id} does not end at depot"
            )

    # --- 4. Fleet size ------------------------------------------------------
    if len(solution.routes) > instance.n_vehicles:
        violations.append(
            f"Number of routes ({len(solution.routes)}) exceeds "
            f"fleet size ({instance.n_vehicles})"
        )

    return FeasibilityReport(
        feasible=len(violations) == 0,
        violations=tuple(violations),
    )