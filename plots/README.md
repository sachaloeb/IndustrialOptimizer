# plots/

Benchmark figure generation scripts. Reads logged trajectory data (does not re-solve).

## B&B Trajectory Plot

```bash
python plots/plot_bnb.py                              # auto-pick a trajectory from bench/results/
python plots/plot_bnb.py --trajectory path/to/traj.csv # explicit trajectory
python plots/plot_bnb.py --out my_plot.png             # custom output path
```

Requires `matplotlib` (`pip install -e ".[plots]"`).

Planned for Weeks 4+: heuristic comparison plots, convergence charts.