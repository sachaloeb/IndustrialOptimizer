"""Tests for JSON instance round-trip serialisation."""

import json
import tempfile
from pathlib import Path

from industrial_optimizer.generator import generate_instance
from industrial_optimizer.io import (
    instance_from_dict,
    instance_to_dict,
    load_instance,
    save_instance,
)


def test_instance_round_trip_via_file() -> None:
    """Save → load produces an identical Instance (all fields preserved)."""
    instance = generate_instance(
        n_customers=5,
        grid_size=100,
        demand_low=1,
        demand_high=10,
        capacity=30,
        n_vehicles=3,
        seed=42,
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "test_instance.json"
        save_instance(instance, path)
        loaded = load_instance(path)

    assert instance == loaded


def test_instance_round_trip_via_dict() -> None:
    """to_dict → from_dict produces an identical Instance."""
    instance = generate_instance(
        n_customers=8,
        grid_size=200,
        demand_low=2,
        demand_high=15,
        capacity=50,
        n_vehicles=4,
        seed=99,
    )
    data = instance_to_dict(instance)
    restored = instance_from_dict(data)
    assert instance == restored


def test_json_contains_all_fields() -> None:
    """The JSON representation includes every field, including None tw values."""
    instance = generate_instance(
        n_customers=3,
        grid_size=50,
        demand_low=1,
        demand_high=5,
        capacity=20,
        n_vehicles=2,
        seed=7,
    )
    data = instance_to_dict(instance)
    raw = json.dumps(data)

    # Spot-check key fields exist
    assert "format_version" in raw
    assert "depot" in raw
    assert "tw_start" in raw
    assert "tw_end" in raw
    assert "customers" in raw
    assert "vehicles" in raw