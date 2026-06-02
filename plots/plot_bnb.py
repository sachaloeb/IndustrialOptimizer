#!/usr/bin/env python3
"""Plot Branch-and-Bound trajectory: incumbent and best-bound vs. time.

Reads a trajectory CSV (columns: time_s, incumbent, best_bound, nodes)
and produces a PNG showing incumbent value (step), best-bound (step),
and the shaded gap between them.

Usage::

    python plots/plot_bnb.py                          # auto-pick trajectory
    python plots/plot_bnb.py --trajectory <path.csv>  # explicit file
    python plots/plot_bnb.py --out my_plot.png         # custom output path
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt  # type: ignore[import-untyped]


def _read_trajectory(
    path: Path,
) -> tuple[list[float], list[float | None], list[float | None]]:
    """Read a trajectory CSV and return (times, incumbents, bounds)."""
    times: list[float] = []
    incumbents: list[float | None] = []
    bounds: list[float | None] = []

    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            times.append(float(row["time_s"]))
            inc_str = row["incumbent"].strip()
            incumbents.append(float(inc_str) if inc_str else None)
            bound_str = row["best_bound"].strip()
            bounds.append(float(bound_str) if bound_str else None)

    return times, incumbents, bounds


def _find_default_trajectory() -> Path:
    """Pick a representative trajectory from bench/results/trajectories/.

    Prefers large/medium tiers at 60s budget, falling back to whatever
    is available.
    """
    traj_dir = Path(__file__).resolve().parent.parent / "bench" / "results" / "trajectories"
    if not traj_dir.exists():
        print(
            "No trajectories found. Run bench/run_benchmark.py first.",
            file=sys.stderr,
        )
        sys.exit(1)

    candidates = list(traj_dir.glob("*.csv"))
    if not candidates:
        print("No trajectory CSVs found.", file=sys.stderr)
        sys.exit(1)

    # Prefer 60s budget, then 10s, then anything.
    for suffix in ("__60s.csv", "__10s.csv"):
        matched = [c for c in candidates if c.name.endswith(suffix)]
        if matched:
            # Prefer larger instances (higher n in the filename).
            matched.sort(key=lambda p: p.name, reverse=True)
            return matched[0]

    return sorted(candidates, key=lambda p: p.name, reverse=True)[0]


def plot_bnb(
    traj_path: Path,
    out_path: Path | None = None,
) -> Path:
    """Create a B&B trajectory plot and return the output path.

    Args:
        traj_path: Path to the trajectory CSV.
        out_path: Output PNG path.  Defaults to ``plots/<stem>.png``.

    Returns:
        The path to the saved PNG.
    """
    times, incumbents, bounds = _read_trajectory(traj_path)

    if not times:
        print("Empty trajectory — nothing to plot.", file=sys.stderr)
        sys.exit(1)

    # Build step-function series: carry forward last known value.
    inc_times: list[float] = []
    inc_vals: list[float] = []
    last_inc: float | None = None
    for t, v in zip(times, incumbents):
        if v is not None:
            last_inc = v
        if last_inc is not None:
            inc_times.append(t)
            inc_vals.append(last_inc)

    bound_times: list[float] = []
    bound_vals: list[float] = []
    last_bound: float | None = None
    for t, v in zip(times, bounds):
        if v is not None:
            last_bound = v
        if last_bound is not None:
            bound_times.append(t)
            bound_vals.append(last_bound)

    # Plot.
    fig, ax = plt.subplots(figsize=(8, 5))

    if inc_times:
        ax.step(inc_times, inc_vals, where="post", label="Incumbent",
                color="#d62728", linewidth=2)
    if bound_times:
        ax.step(bound_times, bound_vals, where="post", label="Best bound",
                color="#1f77b4", linewidth=2)

    # Shade the gap where both series overlap.
    if inc_times and bound_times:
        # Build aligned series for fill_between.
        all_t = sorted(set(inc_times) | set(bound_times))
        aligned_inc: list[float] = []
        aligned_bound: list[float] = []
        ci, cb = 0, 0
        cur_inc: float | None = None
        cur_bound: float | None = None
        for t in all_t:
            while ci < len(inc_times) and inc_times[ci] <= t:
                cur_inc = inc_vals[ci]
                ci += 1
            while cb < len(bound_times) and bound_times[cb] <= t:
                cur_bound = bound_vals[cb]
                cb += 1
            aligned_inc.append(cur_inc if cur_inc is not None else float("nan"))
            aligned_bound.append(cur_bound if cur_bound is not None else float("nan"))

        ax.fill_between(
            all_t, aligned_bound, aligned_inc,
            alpha=0.15, color="#9467bd", label="Gap",
            step="post",
        )

    ax.set_xlabel("Wall-clock time (s)")
    ax.set_ylabel("Objective value")
    instance_name = traj_path.stem.rsplit("__", 1)[0]
    ax.set_title(f"B&B trajectory — {instance_name}")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    if out_path is None:
        out_path = Path(__file__).resolve().parent / f"{traj_path.stem}.png"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out_path), dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved plot to {out_path}")
    return out_path


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Plot B&B incumbent/bound trajectory.",
    )
    parser.add_argument(
        "--trajectory",
        type=Path,
        default=None,
        help="Path to trajectory CSV (auto-detected if omitted).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output PNG path (default: plots/<name>.png).",
    )
    args = parser.parse_args(argv)

    traj_path = args.trajectory or _find_default_trajectory()
    plot_bnb(traj_path, args.out)


if __name__ == "__main__":
    main()