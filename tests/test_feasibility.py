"""Tests for the feasibility checker.

Uses a hand-crafted 3-customer instance with known demands so that
feasibility boundaries are exact and easy to reason about.
"""

from src.industrial_optimizer.feasibility import check_feasibility
from src.industrial_optimizer.models import (
    Instance,
    Node,
    Route,
    Solution,
    Vehicle,
)

# ---------------------------------------------------------------------------
# Shared fixture: 3 customers, 2 vehicles, capacity 20
#   Customer 1: demand 5
#   Customer 2: demand 10
#   Customer 3: demand 8
# ---------------------------------------------------------------------------

_DEPOT = Node(id=0, x=0.0, y=0.0, demand=0)
_CUSTOMERS = (
    Node(id=1, x=1.0, y=0.0, demand=5),
    Node(id=2, x=0.0, y=1.0, demand=10),
    Node(id=3, x=1.0, y=1.0, demand=8),
)
_VEHICLES = (Vehicle(id=0, capacity=20), Vehicle(id=1, capacity=20))
_INSTANCE = Instance(
    name="test_feasibility",
    depot=_DEPOT,
    customers=_CUSTOMERS,
    vehicles=_VEHICLES,
)


def test_feasible_solution() -> None:
    """A valid solution passes the checker."""
    solution = Solution(
        instance_name="test_feasibility",
        routes=(
            Route(vehicle_id=0, node_ids=(0, 1, 2, 0)),  # load 15 <= 20
            Route(vehicle_id=1, node_ids=(0, 3, 0)),      # load  8 <= 20
        ),
    )
    report = check_feasibility(_INSTANCE, solution)
    assert report.feasible
    assert len(report.violations) == 0


def test_unvisited_customer() -> None:
    """Omitting customer 2 is detected."""
    solution = Solution(
        instance_name="test_feasibility",
        routes=(
            Route(vehicle_id=0, node_ids=(0, 1, 0)),
            Route(vehicle_id=1, node_ids=(0, 3, 0)),
        ),
    )
    report = check_feasibility(_INSTANCE, solution)
    assert not report.feasible
    assert any("Unvisited" in v for v in report.violations)


def test_capacity_overflow() -> None:
    """Putting all customers on one route exceeds capacity (23 > 20)."""
    solution = Solution(
        instance_name="test_feasibility",
        routes=(
            Route(vehicle_id=0, node_ids=(0, 1, 2, 3, 0)),  # load 23 > 20
        ),
    )
    report = check_feasibility(_INSTANCE, solution)
    assert not report.feasible
    assert any("exceeds capacity" in v for v in report.violations)


def test_route_not_closed_at_depot() -> None:
    """A route that does not return to the depot is rejected."""
    solution = Solution(
        instance_name="test_feasibility",
        routes=(
            Route(vehicle_id=0, node_ids=(0, 1, 2)),   # missing return to depot
            Route(vehicle_id=1, node_ids=(0, 3, 0)),
        ),
    )
    report = check_feasibility(_INSTANCE, solution)
    assert not report.feasible
    assert any("does not end at depot" in v for v in report.violations)
