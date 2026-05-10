"""Deterministic CVRP instance generator.

All randomness is driven by a single :class:`random.Random` instance seeded
with the caller-supplied ``seed``.  Same parameters + same seed = byte-identical
JSON output (within a given Python minor version).
"""

import random as _random_mod

from .models import Instance, Node, Vehicle


def generate_instance(
    *,
    n_customers: int,
    grid_size: int,
    demand_low: int,
    demand_high: int,
    capacity: int,
    n_vehicles: int,
    seed: int,
    name: str | None = None,
) -> Instance:
    """Generate a random CVRP instance.

    Args:
        n_customers: Number of customer nodes (excluding depot).
        grid_size: Coordinates are drawn from ``[0, grid_size]``.
        demand_low: Minimum customer demand (inclusive).
        demand_high: Maximum customer demand (inclusive).
        capacity: Uniform vehicle capacity.
        n_vehicles: Number of vehicles in the fleet.
        seed: RNG seed for full reproducibility.
        name: Optional instance name (auto-generated if *None*).

    Returns:
        A fully-specified :class:`Instance`.
    """
    rng = _random_mod.Random(seed)

    depot = Node(
        id=0,
        x=rng.uniform(0.0, float(grid_size)),
        y=rng.uniform(0.0, float(grid_size)),
        demand=0,
    )

    customers: list[Node] = []
    for i in range(1, n_customers + 1):
        customers.append(
            Node(
                id=i,
                x=rng.uniform(0.0, float(grid_size)),
                y=rng.uniform(0.0, float(grid_size)),
                demand=rng.randint(demand_low, demand_high),
            )
        )

    vehicles = tuple(
        Vehicle(id=v, capacity=capacity) for v in range(n_vehicles)
    )

    instance_name = name if name is not None else f"cvrp_n{n_customers}_s{seed}"

    return Instance(
        name=instance_name,
        depot=depot,
        customers=tuple(customers),
        vehicles=vehicles,
    )