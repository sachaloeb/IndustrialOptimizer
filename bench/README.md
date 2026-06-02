# bench/

Benchmark runner CLI for CVRP solvers. Sweeps instance sizes × seeds × time budgets and logs results to CSV with per-run B&B trajectory data.

## Usage

```bash
python bench/run_benchmark.py              # full sweep (small/medium/large × 5 seeds × {1,10,60}s)
python bench/run_benchmark.py --quick      # minimal smoke-test sweep
python bench/run_benchmark.py --out dir    # custom output directory
```

## Output

- `results/results.csv` — one row per (method, instance, time_budget) with objective, gap, node count, etc.
- `results/trajectories/<instance>__<budget>s.csv` — B&B trajectory (time, incumbent, best_bound, nodes).
- `results/run_meta.json` — environment info (PuLP/CBC/Python versions, sweep config).

The CSV schema includes a `method` column so that future heuristic results (Week 4) append rows without schema changes.