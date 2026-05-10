"""Industrial-grade Capacitated Vehicle Routing Problem (CVRP) optimizer.

This package provides data models, a deterministic instance generator,
a PuLP-based MILP builder (two-index + MTZ), and a feasibility checker.
Heuristics and benchmark tooling are planned for later weeks.
"""

from .feasibility import check_feasibility as check_feasibility
from .generator import generate_instance as generate_instance
from .io import (
    instance_from_dict as instance_from_dict,
    instance_to_dict as instance_to_dict,
    load_instance as load_instance,
    save_instance as save_instance,
)
from .milp import build_cvrp_model as build_cvrp_model
from .models import (
    FeasibilityReport as FeasibilityReport,
    Instance as Instance,
    Node as Node,
    Route as Route,
    Solution as Solution,
    Vehicle as Vehicle,
    compute_distance_matrix as compute_distance_matrix,
    euclidean_distance as euclidean_distance,
)

__all__ = [
    "Node",
    "Vehicle",
    "Instance",
    "Route",
    "Solution",
    "FeasibilityReport",
    "euclidean_distance",
    "compute_distance_matrix",
    "instance_to_dict",
    "instance_from_dict",
    "save_instance",
    "load_instance",
    "generate_instance",
    "build_cvrp_model",
    "check_feasibility",
]