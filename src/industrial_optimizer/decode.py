"""Decode arc-variable values into a CVRP Solution.

This module is solver-agnostic: it operates on a mapping of
``(i, j) -> float`` arc values and reconstructs depot-closed routes.
It is reused by both the MILP solver and future heuristics.
"""

from __future__ import annotations

from .models import (
    Instance,
    Route,
    Solution,
    compute_distance_matrix,
)


def decode_solution(
    instance: Instance,
    x_values: dict[tuple[int, int], float],
    *,
    vehicle_ids: list[int] | None = None,
    round_distances: bool = False,
) -> Solution:
    """Build a :class:`Solution` from arc-variable values.

    Args:
        instance: The CVRP instance being solved.
        x_values: Mapping ``(i, j) -> value`` for arc variables.
            Arcs with value > 0.5 are treated as selected.
        vehicle_ids: Optional explicit vehicle ID assignment.  If
            *None*, vehicles are numbered ``0 .. m-1``.
        round_distances: Whether to round distances (for consistency
            with the objective that was optimised).

    Returns:
        A feasible :class:`Solution` with depot-closed routes.
    """
    depot_id = instance.depot.id

    # Build successor map from selected arcs.
    # The depot may have multiple out-arcs, so we use a list-based
    # adjacency for it and a simple dict for customers.
    customer_successor: dict[int, int] = {}
    depot_out: list[int] = []
    for (i, j), val in x_values.items():
        if val > 0.5:
            if i == depot_id:
                depot_out.append(j)
            else:
                customer_successor[i] = j

    depot_out.sort()  # deterministic ordering

    # Trace routes starting from each depot out-arc.
    routes: list[Route] = []
    vid_iter = iter(vehicle_ids) if vehicle_ids is not None else None
    route_index = 0

    for first_customer in depot_out:
        if first_customer == depot_id:
            continue  # skip empty self-loop (shouldn't happen)

        path: list[int] = [depot_id, first_customer]
        current = first_customer
        while current != depot_id:
            nxt = customer_successor.get(current)
            if nxt is None:
                break  # broken chain — stop gracefully
            path.append(nxt)
            current = nxt

        vid = next(vid_iter) if vid_iter is not None else route_index
        routes.append(Route(vehicle_id=vid, node_ids=tuple(path)))
        route_index += 1

    # Compute total distance.
    dist = compute_distance_matrix(
        instance.all_nodes, round_distances=round_distances,
    )
    total = 0.0
    for route in routes:
        for k in range(len(route.node_ids) - 1):
            a, b = route.node_ids[k], route.node_ids[k + 1]
            total += dist[a, b]

    return Solution(
        instance_name=instance.name,
        routes=tuple(routes),
        total_distance=total,
    )