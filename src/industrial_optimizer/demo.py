"""Demo script: generate instance -> JSON round-trip -> build MILP -> check feasibility.

Run with::

    python -m industrial_optimizer.demo

This script does **not** solve the MILP; it only demonstrates the data
pipeline and model construction implemented in Weeks 1-2.
"""

from pathlib import Path

from .feasibility import check_feasibility
from .generator import generate_instance
from .io import load_instance, save_instance
from .milp import build_cvrp_model
from .models import Instance, Route, Solution

# Demo parameters -- small enough to print, large enough to exercise the code.
DEMO_N_CUSTOMERS = 5
DEMO_GRID_SIZE = 100
DEMO_DEMAND_LOW = 1
DEMO_DEMAND_HIGH = 10
DEMO_CAPACITY = 30
DEMO_N_VEHICLES = 3
DEMO_SEED = 42

SAMPLE_PATH = (
    Path(__file__).resolve().parent.parent.parent / "instances" / "sample.json"
)


def _build_greedy_solution(instance: Instance) -> Solution:
    """First-fit decreasing bin-packing into routes respecting capacity."""
    routes: list[Route] = []
    current_nodes: list[int] = [instance.depot.id]
    current_load = 0
    vehicle_id = 0

    for customer in instance.customers:
        if current_load + customer.demand > instance.capacity:
            # Close current route and start a new one.
            current_nodes.append(instance.depot.id)
            routes.append(
                Route(vehicle_id=vehicle_id, node_ids=tuple(current_nodes))
            )
            vehicle_id += 1
            current_nodes = [instance.depot.id]
            current_load = 0
        current_nodes.append(customer.id)
        current_load += customer.demand

    # Close the last route.
    if len(current_nodes) > 1:
        current_nodes.append(instance.depot.id)
        routes.append(
            Route(vehicle_id=vehicle_id, node_ids=tuple(current_nodes))
        )

    return Solution(instance_name=instance.name, routes=tuple(routes))


def main() -> None:
    """Run the Week 1-2 demo pipeline."""
    # 1. Generate ----------------------------------------------------------
    print("=== Generating CVRP instance ===")
    instance = generate_instance(
        n_customers=DEMO_N_CUSTOMERS,
        grid_size=DEMO_GRID_SIZE,
        demand_low=DEMO_DEMAND_LOW,
        demand_high=DEMO_DEMAND_HIGH,
        capacity=DEMO_CAPACITY,
        n_vehicles=DEMO_N_VEHICLES,
        seed=DEMO_SEED,
    )
    print(
        f"  {instance.name}: {instance.n_customers} customers, "
        f"{instance.n_vehicles} vehicles, capacity {instance.capacity}"
    )

    # 2. Save to JSON ------------------------------------------------------
    SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    save_instance(instance, SAMPLE_PATH)
    print(f"  Saved to {SAMPLE_PATH}")

    # 3. Reload and verify round-trip --------------------------------------
    loaded = load_instance(SAMPLE_PATH)
    assert instance == loaded, "JSON round-trip mismatch!"
    print("  JSON round-trip: OK")

    # 4. Build MILP --------------------------------------------------------
    print("\n=== Building MILP model ===")
    model, variables = build_cvrp_model(instance)
    n_vars = len(variables["x"]) + len(variables["u"])
    n_constraints = len(model.constraints)
    n_obj_terms = len(model.objective)
    print(f"  Variables:       {n_vars}")
    print(f"  Constraints:     {n_constraints}")
    print(f"  Objective terms: {n_obj_terms}")

    # 5. Feasibility check -------------------------------------------------
    print("\n=== Feasibility check ===")
    solution = _build_greedy_solution(instance)
    report = check_feasibility(instance, solution)
    print(f"  Routes: {len(solution.routes)}")
    for route in solution.routes:
        print(f"    Vehicle {route.vehicle_id}: {list(route.node_ids)}")
    print(f"  Feasible: {report.feasible}")
    if not report.feasible:
        for v in report.violations:
            print(f"    VIOLATION: {v}")

    print("\nDone.")


if __name__ == "__main__":
    main()