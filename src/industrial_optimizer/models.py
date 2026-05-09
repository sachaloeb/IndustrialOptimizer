"""Core data models for the Capacitated Vehicle Routing Problem (CVRP).

All domain objects are frozen dataclasses for immutability and hashability.
Structural hooks for time windows (tw_start / tw_end) are present but
not enforced anywhere in v1.
"""

import math
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Domain objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Node:
    """A location in the CVRP graph (depot or customer).

    Attributes:
        id: Unique integer identifier (0 = depot by convention).
        x: Horizontal coordinate in the Euclidean plane.
        y: Vertical coordinate in the Euclidean plane.
        demand: Units of goods to deliver (0 for the depot).
        tw_start: Earliest service start time (optional, unused in v1).
        tw_end: Latest service start time (optional, unused in v1).
    """

    id: int
    x: float
    y: float
    demand: int
    tw_start: float | None = None
    tw_end: float | None = None


@dataclass(frozen=True)
class Vehicle:
    """A vehicle in the homogeneous fleet.

    Attributes:
        id: Unique integer identifier.
        capacity: Maximum load the vehicle can carry.
    """

    id: int
    capacity: int


@dataclass(frozen=True)
class Instance:
    """A complete CVRP problem instance.

    Attributes:
        name: Human-readable instance name.
        depot: The depot node (id 0).
        customers: Tuple of customer nodes.
        vehicles: Tuple of vehicles (homogeneous fleet).
        format_version: Schema version for JSON serialisation.
    """

    name: str
    depot: Node
    customers: tuple[Node, ...]
    vehicles: tuple[Vehicle, ...]
    format_version: int = 1

    @property
    def n_customers(self) -> int:
        """Number of customers in the instance."""
        return len(self.customers)

    @property
    def n_vehicles(self) -> int:
        """Number of vehicles in the fleet."""
        return len(self.vehicles)

    @property
    def capacity(self) -> int:
        """Fleet capacity (homogeneous, taken from the first vehicle)."""
        if not self.vehicles:
            raise ValueError("Instance has no vehicles")
        return self.vehicles[0].capacity

    @property
    def all_nodes(self) -> tuple[Node, ...]:
        """Depot followed by all customers."""
        return (self.depot,) + self.customers


@dataclass(frozen=True)
class Route:
    """An ordered sequence of node IDs visited by one vehicle.

    The sequence must start and end at the depot (node 0).
    """

    vehicle_id: int
    node_ids: tuple[int, ...]


@dataclass(frozen=True)
class Solution:
    """A solution to a CVRP instance.

    Attributes:
        instance_name: Name of the instance this solution belongs to.
        routes: One route per active vehicle.
        total_distance: Cached objective value (None if not computed).
    """

    instance_name: str
    routes: tuple[Route, ...]
    total_distance: float | None = None


@dataclass(frozen=True)
class FeasibilityReport:
    """Result of a feasibility check on a CVRP solution.

    Attributes:
        feasible: True iff no violations were found.
        violations: Human-readable descriptions of each violation.
    """

    feasible: bool
    violations: tuple[str, ...]


# ---------------------------------------------------------------------------
# Distance utilities
# ---------------------------------------------------------------------------

def euclidean_distance(a: Node, b: Node) -> float:
    """Euclidean distance between two nodes."""
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def compute_distance_matrix(
    nodes: tuple[Node, ...],
    *,
    round_distances: bool = False,
) -> dict[tuple[int, int], float]:
    """Compute pairwise distances for all ordered node pairs (i != j).

    Args:
        nodes: All nodes including the depot.
        round_distances: If True, round to the nearest integer
            (CVRPLIB compatibility).

    Returns:
        Mapping from ``(i, j)`` node-ID pairs to distances.
    """
    matrix: dict[tuple[int, int], float] = {}
    for a in nodes:
        for b in nodes:
            if a.id != b.id:
                d = euclidean_distance(a, b)
                if round_distances:
                    d = float(round(d))
                matrix[a.id, b.id] = d
    return matrix