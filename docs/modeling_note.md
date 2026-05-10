# Modelling Note — CVRP v1

## Problem Statement

We are given a single depot, a set of customers each with a known goods demand, and a fleet of identical vehicles with a shared capacity limit. The task is to design a set of routes — each starting and ending at the depot — such that every customer is served exactly once, no vehicle is overloaded, and the total distance travelled is minimised. Distances are Euclidean and deterministic.

## Assumptions

| Assumption | Justification | When it would break |
|---|---|---|
| Single depot | Simplifies the model to standard CVRP; most last-mile distribution operates from one warehouse | Multi-warehouse or cross-docking scenarios require multi-depot extensions |
| Homogeneous fleet | All vehicles share one capacity value, reducing parameters and eliminating vehicle-assignment complexity | Mixed fleets (e.g., vans + trucks) require heterogeneous-capacity constraints |
| Deterministic Euclidean distances | Enables closed-form distance matrix; reproducible benchmarks | Real road networks (asymmetric, traffic-dependent) require graph-based shortest paths |
| No service times | Keeps the model pure CVRP; service times would add time-resource constraints without changing route structure | When total route duration matters (shift limits), service/dwell times become binding |
| No time windows | Structural hooks exist (`Node.tw_start` / `Node.tw_end`) but are not enforced | Customer availability windows require CVRPTW extension with time-tracking variables |
| Demand $\leq$ vehicle capacity | Each customer can be served by a single vehicle; no split delivery | Large-volume customers needing multiple trips require split-delivery CVRP |

## Constraint-by-Constraint Commentary

| Constraint | What it enforces | Effect of removal |
|---|---|---|
| `leave_i` | Every customer is departed from exactly once — ensures full coverage and no revisits | Customers could be skipped or visited multiple times, violating the "visit once" requirement |
| `enter_j` | Every customer is arrived at exactly once — the arrival counterpart to `leave_i` | Unbalanced flow; a customer could be "left" without ever being "entered", producing disconnected arcs |
| `depot_out` | At most $K$ vehicles leave the depot — respects fleet size | Unlimited route count; solver could use arbitrarily many single-customer routes |
| `depot_in` | At most $K$ vehicles return to the depot — symmetric to `depot_out` | Flow imbalance at depot; vehicles could "leave" without "returning", breaking route closure |
| `mtz_i_j` | Subtour elimination and capacity coupling — if arc $(i,j)$ is used, the load at $j$ must account for $j$'s demand on top of the load at $i$ | Disconnected subtours (cycles not passing through the depot) become feasible; capacity is not tracked |
| `bounds_u` | Load variable bounded between customer demand and vehicle capacity | Without the lower bound, the MTZ ordering breaks; without the upper bound, capacity is unenforced |

## Out of Scope (v1)

- **Multi-depot** — requires depot-assignment variables and per-depot fleet limits.
- **Stochastic travel times** — requires robust or chance-constrained formulation.
- **Time windows** — structural hooks (`Node.tw_start`, `Node.tw_end`) exist in `models.py` but are not enforced by any constraint.
- **Heterogeneous fleet** — current model assumes uniform `Vehicle.capacity`.
- **Service times** — no duration tracking on routes.
- **Real WMS integration** — instances are synthetic; no external data pipeline.

## Forward Pointer

Week 3–4 (OR(2)) will add: solving the MILP with CBC, branch-and-bound trajectory logging, a first greedy heuristic baseline, and the initial benchmark sweep across instance sizes.
