"""Tests for the CBC solver wrapper."""

import pytest

from industrial_optimizer.feasibility import check_feasibility
from industrial_optimizer.generator import generate_instance
from industrial_optimizer.solver import SolveResult, lp_relaxation_bound, solve_cvrp


@pytest.fixture()
def tiny_instance():
    """A very small instance that CBC can solve optimally in <1s."""
    return generate_instance(
        n_customers=5,
        grid_size=100,
        demand_low=1,
        demand_high=10,
        capacity=50,
        n_vehicles=5,
        seed=7,
    )


def test_solve_optimal(tiny_instance) -> None:
    """Solve a tiny instance and verify optimality + feasibility."""
    result = solve_cvrp(tiny_instance, time_limit=30)

    assert result.status == "Optimal"
    assert result.best_objective is not None
    assert result.best_objective > 0
    assert result.wall_time_s > 0
    assert result.feasible is True
    assert result.solution is not None
    assert result.instance_name == tiny_instance.name
    assert result.n_customers == tiny_instance.n_customers


def test_lp_bound_leq_objective(tiny_instance) -> None:
    """LP relaxation bound must be <= the MILP optimal objective."""
    result = solve_cvrp(tiny_instance, time_limit=30)
    lp_bound = result.lp_relaxation_bound

    assert lp_bound is not None
    assert result.best_objective is not None
    # LP relaxation is a lower bound (minimisation problem).
    assert lp_bound <= result.best_objective + 1e-6


def test_feasibility_of_decoded_solution(tiny_instance) -> None:
    """The decoded solution passes the independent feasibility checker."""
    result = solve_cvrp(tiny_instance, time_limit=30)
    assert result.solution is not None
    report = check_feasibility(tiny_instance, result.solution)
    assert report.feasible, f"Violations: {report.violations}"


def test_solve_result_fields(tiny_instance) -> None:
    """SolveResult has all expected fields populated."""
    result = solve_cvrp(tiny_instance, time_limit=30)

    assert isinstance(result, SolveResult)
    assert result.n_nodes is None or result.n_nodes >= 0
    assert result.lp_relaxation_bound is not None
    assert result.lp_relaxation_bound > 0


def test_lp_relaxation_standalone(tiny_instance) -> None:
    """lp_relaxation_bound() works as standalone function."""
    bound = lp_relaxation_bound(tiny_instance)
    assert bound > 0