"""Tests for bench_engines: SQL/frame builders, aggregation, and verdict logic without engines installed."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "bench_engines.py"
SPEC = importlib.util.spec_from_file_location("bench_engines", SCRIPT)
bench_engines = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["bench_engines"] = bench_engines
SPEC.loader.exec_module(bench_engines)


@pytest.mark.parametrize("workload", bench_engines.WORKLOADS)
def test_duckdb_sql_covers_every_workload(workload: str) -> None:
    statement = bench_engines.duckdb_sql(workload, "data/*.parquet", "region", "amount")
    assert "read_parquet('data/*.parquet')" in statement
    assert "amount" in statement


def test_summarize_medians_and_cv() -> None:
    records = [
        {"engine": "polars", "version": "2.0.0", "seconds": 1.0, "peak_rss_mb": 100.0},
        {"engine": "polars", "version": "2.0.0", "seconds": 2.0, "peak_rss_mb": 120.0},
        {"engine": "polars", "version": "2.0.0", "seconds": 3.0, "peak_rss_mb": 110.0},
    ]
    summary = bench_engines.summarize(records)
    assert summary["ok"] is True
    assert summary["median_seconds"] == 2.0
    assert summary["peak_rss_mb"] == 120.0
    assert summary["cv"] == pytest.approx(0.5)


def test_summarize_reports_failure() -> None:
    summary = bench_engines.summarize([{"engine": "duckdb", "error": "boom"}])
    assert summary == {"ok": False, "error": "boom", "version": None}


def summary(median: float, rss: float, cv: float = 0.01) -> dict:  # style:allow shared by verdict cases
    return {
        "ok": True,
        "version": "x",
        "runs": 3,
        "median_seconds": median,
        "mean_seconds": median,
        "cv": cv,
        "peak_rss_mb": rss,
    }


def test_verdict_reports_winners() -> None:
    outcome = bench_engines.verdict(summary(1.0, 100.0), summary(2.0, 300.0))
    assert "time: polars" in outcome
    assert "memory: polars" in outcome


def test_verdict_ties_within_ten_percent() -> None:
    outcome = bench_engines.verdict(summary(1.0, 100.0), summary(1.05, 105.0))
    assert "time: tie" in outcome
    assert "memory: tie" in outcome


def test_verdict_flags_variance() -> None:
    outcome = bench_engines.verdict(summary(1.0, 100.0, cv=0.5), summary(2.0, 200.0))
    assert "inconclusive" in outcome


def test_verdict_reports_incomplete() -> None:
    outcome = bench_engines.verdict(summary(1.0, 100.0), {"ok": False, "error": "missing duckdb"})
    assert outcome.startswith("incomplete: duckdb failed")


def test_cli_rejects_missing_input() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--data", "definitely-not-here-*.parquet"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "no Parquet input matches" in result.stderr
