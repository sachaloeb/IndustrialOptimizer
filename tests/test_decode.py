"""Tests for the arc-variable decoder."""

from industrial_optimizer.decode import decode_solution
from industrial_optimizer.models import Instance, Node, Route, Vehicle


def _make_instance() -> Instance:
    """3-customer instance with known geometry."""
    return Instance(
        name="test_decode",
        depot=Node(id=0, x=0.0, y=0.0, demand=0),
        customers=(
            Node(id=1, x=1.0, y=0.0, demand=5),
            Node(id=2, x=0.0, y=1.0, demand=5),
            Node(id=3, x=1.0, y=1.0, demand=5),
        ),
        vehicles=(
            Vehicle(id=0, capacity=20),
            Vehicle(id=1, capacity=20),
        ),
    )


def test_single_route_all_customers() -> None:
    """All customers on one route: 0 -> 1 -> 3 -> 2 -> 0."""
    inst = _make_instance()
    x_vals: dict[tuple[int, int], float] = {
        (0, 1): 1.0,
        (1, 3): 1.0,
        (3, 2): 1.0,
        (2, 0): 1.0,
    }
    sol = decode_solution(inst, x_vals)

    assert len(sol.routes) == 1
    assert sol.routes[0].node_ids == (0, 1, 3, 2, 0)
    assert sol.routes[0].node_ids[0] == 0
    assert sol.routes[0].node_ids[-1] == 0
    assert sol.total_distance is not None
    assert sol.total_distance > 0


def test_two_routes() -> None:
    """Two routes: 0->1->0 and 0->2->3->0."""
    inst = _make_instance()
    x_vals: dict[tuple[int, int], float] = {
        (0, 1): 1.0,
        (1, 0): 1.0,
        (0, 2): 1.0,
        (2, 3): 1.0,
        (3, 0): 1.0,
    }
    sol = decode_solution(inst, x_vals)

    assert len(sol.routes) == 2
    # Both routes start and end at depot.
    for route in sol.routes:
        assert route.node_ids[0] == 0
        assert route.node_ids[-1] == 0

    # All customers visited.
    visited = set()
    for route in sol.routes:
        for nid in route.node_ids:
            if nid != 0:
                visited.add(nid)
    assert visited == {1, 2, 3}


def test_ignores_fractional_arcs() -> None:
    """Arcs with value <= 0.5 are ignored."""
    inst = _make_instance()
    x_vals: dict[tuple[int, int], float] = {
        (0, 1): 1.0,
        (1, 2): 1.0,
        (2, 0): 1.0,
        # fractional noise
        (0, 3): 0.3,
        (3, 0): 0.3,
    }
    sol = decode_solution(inst, x_vals)
    assert len(sol.routes) == 1
    visited = {nid for r in sol.routes for nid in r.node_ids if nid != 0}
    assert 3 not in visited


def test_vehicle_ids_assigned() -> None:
    """Explicit vehicle_ids are respected."""
    inst = _make_instance()
    x_vals: dict[tuple[int, int], float] = {
        (0, 1): 1.0,
        (1, 0): 1.0,
        (0, 2): 1.0,
        (2, 0): 1.0,
    }
    sol = decode_solution(inst, x_vals, vehicle_ids=[10, 20])
    assert sol.routes[0].vehicle_id == 10
    assert sol.routes[1].vehicle_id == 20


def test_depot_closure() -> None:
    """Every decoded route starts and ends at depot 0."""
    inst = _make_instance()
    x_vals: dict[tuple[int, int], float] = {
        (0, 1): 1.0,
        (1, 3): 1.0,
        (3, 0): 1.0,
        (0, 2): 1.0,
        (2, 0): 1.0,
    }
    sol = decode_solution(inst, x_vals)
    for route in sol.routes:
        assert route.node_ids[0] == 0, "Route must start at depot"
        assert route.node_ids[-1] == 0, "Route must end at depot"