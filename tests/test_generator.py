"""Tests for deterministic instance generation."""

import json

from industrial_optimizer.generator import generate_instance
from industrial_optimizer.io import instance_to_dict


def test_same_seed_byte_identical() -> None:
    """Two calls with the same parameters and seed produce byte-identical JSON."""
    kwargs = dict(
        n_customers=10,
        grid_size=100,
        demand_low=1,
        demand_high=20,
        capacity=50,
        n_vehicles=5,
        seed=123,
    )
    inst_a = generate_instance(**kwargs)
    inst_b = generate_instance(**kwargs)

    json_a = json.dumps(instance_to_dict(inst_a), indent=2)
    json_b = json.dumps(instance_to_dict(inst_b), indent=2)

    assert json_a == json_b


def test_different_seeds_differ() -> None:
    """Different seeds produce different instances."""
    common = dict(
        n_customers=5,
        grid_size=100,
        demand_low=1,
        demand_high=10,
        capacity=30,
        n_vehicles=3,
    )
    inst_a = generate_instance(seed=1, **common)
    inst_b = generate_instance(seed=2, **common)

    assert inst_a != inst_b


def test_generated_instance_structure() -> None:
    """Basic structural invariants hold on a generated instance."""
    inst = generate_instance(
        n_customers=7,
        grid_size=200,
        demand_low=3,
        demand_high=12,
        capacity=40,
        n_vehicles=4,
        seed=0,
    )
    assert inst.depot.id == 0
    assert inst.depot.demand == 0
    assert inst.n_customers == 7
    assert inst.n_vehicles == 4
    assert all(3 <= c.demand <= 12 for c in inst.customers)
    assert all(0.0 <= c.x <= 200.0 for c in inst.customers)
    assert all(0.0 <= c.y <= 200.0 for c in inst.customers)
    assert inst.format_version == 1
