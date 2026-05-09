# IndustrialOptimizer

Industrial-grade Capacitated Vehicle Routing Problem (CVRP) solver combining exact MILP optimisation with heuristic baselines and a reproducible benchmark harness.

## Problem Definition

Given a set of customers with known demands, a depot, and a homogeneous fleet of capacity-limited vehicles, find a set of routes that:

- starts and ends each route at the depot,
- visits every customer exactly once,
- respects vehicle capacity on every route, and
- minimises total travel distance (Euclidean).

The MILP formulation uses a **two-index model with MTZ subtour elimination**, built with [PuLP](https://github.com/coin-or/pulp) (CBC as the default solver).

## Current Scope (Weeks 1-2)

| Delivered | Description |
|-----------|-------------|
| Data model | Typed dataclasses: `Node`, `Vehicle`, `Instance`, `Route`, `Solution`, `FeasibilityReport` |
| JSON I/O | Versioned instance format (`format_version: 1`) with round-trip safety |
| Instance generator | Deterministic (seeded) synthetic CVRP instances with configurable knobs |
| MILP builder | Two-index CVRP + MTZ subtour elimination; builds model, does **not** solve |
| Feasibility checker | Validates solutions against instances (coverage, capacity, depot closure, fleet size) |
| Tests | `pytest` smoke tests for all components |

### What is NOT in v1

- Solving the MILP (Week 3-4).
- Benchmark runner / CSV result logging (Week 3-4).
- Heuristics — greedy construction + local search (Week 5-6).
- Route visualisation / GIF export (Week 5-6).
- Multi-depot, stochastic travel times, time-window constraints, real WMS integration.

## Installation

```bash
# Clone and install in editable mode
git clone <repo-url> && cd IndustrialOptimizer
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Requires **Python >= 3.11**.

## Quick Start

```bash
# Run the demo pipeline (generate -> save JSON -> load -> build MILP -> check feasibility)
python -m industrial_optimizer.demo

# Run tests
pytest -q
```

## Project Structure

```
IndustrialOptimizer/
├── src/industrial_optimizer/   # Core package
│   ├── __init__.py             # Public API re-exports
│   ├── models.py               # Dataclasses + distance utilities
│   ├── io.py                   # JSON serialisation / deserialisation
│   ├── generator.py            # Deterministic instance generator
│   ├── milp.py                 # MILP builder (PuLP, two-index + MTZ)
│   ├── feasibility.py          # Solver-independent feasibility checker
│   └── demo.py                 # End-to-end demo script
├── instances/                  # Generated / loaded problem instances
├── bench/                      # Benchmark runner + CSV logs (Week 3-4)
├── plots/                      # Benchmark figures (Week 3-4)
├── viz/                        # Route visualisation + GIF export (Week 5-6)
├── tests/                      # pytest test suite
├── pyproject.toml              # Build config, dependencies, tool settings
└── README.md
```

## Roadmap

| Week | Focus | Key Deliverables |
|------|-------|-----------------|
| 1-2 | Modelling foundations | Data model, JSON I/O, generator, MILP builder, feasibility checker |
| 3-4 | MILP solving + benchmarks | Solver wrapper, CSV logging, first benchmark sweep, benchmark plots |
| 5-6 | Heuristics + visualisation | Greedy + local-search heuristic, route visualiser, GIF export, MILP vs heuristic comparison |
| 7-8 | Hardening + packaging | Expanded benchmarks, documentation, environment pinning, LinkedIn assets, technical write-up |

## License

MIT — see [LICENSE](LICENSE).
