"""Tests for the MILP builder."""

from industrial_optimizer.generator import generate_instance
from industrial_optimizer.milp import build_cvrp_model


def test_milp_builder_5_customers() -> None:
    """MILP on a 5-customer instance has the expected variable/constraint counts.

    With 6 nodes (depot + 5 customers):
      - x variables: 6 * 5 = 30  (all ordered pairs, no self-loops)
      - u variables: 5            (one per customer)
      - Constraints:
          5  (leave each customer once)
        + 5  (enter each customer once)
        + 1  (depot out-degree)
        + 1  (depot in-degree)
        + 20 (MTZ: 5*4 customer pairs)
        = 32
      - Objective terms: 30 (one per x variable)
    """
    instance = generate_instance(
        n_customers=5,
        grid_size=100,
        demand_low=1,
        demand_high=10,
        capacity=30,
        n_vehicles=3,
        seed=42,
    )
    model, variables = build_cvrp_model(instance)

    assert len(variables["x"]) == 30
    assert len(variables["u"]) == 5
    assert len(model.constraints) == 32
    assert len(model.objective) == 30


def test_milp_builder_no_error_various_sizes() -> None:
    """Model builds without error on several instance sizes."""
    for n in (3, 10, 15):
        instance = generate_instance(
            n_customers=n,
            grid_size=100,
            demand_low=1,
            demand_high=10,
            capacity=50,
            n_vehicles=n,
            seed=0,
        )
        model, variables = build_cvrp_model(instance)
        n_nodes = n + 1
        expected_x = n_nodes * (n_nodes - 1)
        assert len(variables["x"]) == expected_x
        assert len(variables["u"]) == n


def test_milp_round_distances_flag() -> None:
    """The round_distances flag produces a model without error."""
    instance = generate_instance(
        n_customers=5,
        grid_size=100,
        demand_low=1,
        demand_high=10,
        capacity=30,
        n_vehicles=3,
        seed=42,
    )
    model_float, _ = build_cvrp_model(instance, round_distances=False)
    model_int, _ = build_cvrp_model(instance, round_distances=True)

    # Both models should have the same structure.
    assert len(model_float.constraints) == len(model_int.constraints)
