"""Smoke test for the benchmark runner."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

# Ensure bench/ is importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bench"))

from run_benchmark import CSV_HEADER, main  # noqa: E402


@pytest.fixture()
def tmp_out(tmp_path: Path) -> Path:
    """Temporary output directory."""
    return tmp_path / "bench_out"


def test_quick_sweep_produces_csv(tmp_out: Path) -> None:
    """--quick writes a valid results.csv with expected header and data."""
    main(["--quick", "--out", str(tmp_out)])

    csv_path = tmp_out / "results.csv"
    assert csv_path.exists(), "results.csv not created"

    with csv_path.open() as f:
        reader = csv.reader(f)
        header = next(reader)
        assert tuple(header) == CSV_HEADER

        rows = list(reader)
        assert len(rows) >= 1, "Expected at least 1 data row"

        # Check method column.
        for row in rows:
            assert row[0] == "milp"


def test_quick_sweep_produces_meta(tmp_out: Path) -> None:
    """--quick writes a valid run_meta.json."""
    main(["--quick", "--out", str(tmp_out)])

    meta_path = tmp_out / "run_meta.json"
    assert meta_path.exists(), "run_meta.json not created"

    meta = json.loads(meta_path.read_text())
    assert "python_version" in meta
    assert "pulp_version" in meta
    assert "tiers" in meta


def test_quick_sweep_produces_trajectories(tmp_out: Path) -> None:
    """--quick writes trajectory CSVs."""
    main(["--quick", "--out", str(tmp_out)])

    traj_dir = tmp_out / "trajectories"
    assert traj_dir.exists(), "trajectories/ not created"
    traj_files = list(traj_dir.glob("*.csv"))
    assert len(traj_files) >= 1, "Expected at least 1 trajectory CSV"