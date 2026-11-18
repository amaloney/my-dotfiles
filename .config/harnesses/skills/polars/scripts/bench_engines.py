#!/usr/bin/env python3
"""Benchmark Polars against DuckDB on one Parquet input and one built-in workload.

Each run happens in a fresh subprocess so allocator state, thread pools, and imports do not leak between engines.
Reports wall time and peak RSS per engine, then a verdict. See references/benchmark-methodology.md.

Usage:
  bench_engines.py --data events/*.parquet --workload groupby --group-col region --value-col amount
  bench_engines.py --data data.parquet --workload sort --value-col ts --repeat 7 --json result.json
  bench_engines.py --data data.parquet --workload groupby --duckdb-memory-limit 2GB

A verdict is evidence for the decision matrix in references/duckdb-vs-polars.md; it is not a rewrite order.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

WORKLOADS = ("scan_agg", "filter_agg", "groupby", "sort", "join")
TIE_RATIO = 1.10


def peak_rss_mb() -> float:
    """Return this process's peak resident set size in MiB.

    Args:
        None.

    Returns:
        Peak RSS in MiB, normalized across macOS (bytes) and Linux (kilobytes).
    """
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    divisor = 1024 * 1024 if sys.platform == "darwin" else 1024
    return peak / divisor


def duckdb_sql(workload: str, data: str, group_col: str, value_col: str) -> str:
    """Build the SQL for a workload against a Parquet path or glob.

    Args:
        workload: One of WORKLOADS.
        data: Parquet path or glob.
        group_col: Grouping/key column.
        value_col: Numeric value column.

    Returns:
        SQL string.
    """
    source = f"read_parquet('{data}')"
    aggregations = {
        "scan_agg": f"SELECT sum({value_col}) AS total FROM {source}",
        "filter_agg": f"SELECT count(*) AS n FROM {source} WHERE {value_col} > 0",
        "groupby": f"SELECT {group_col}, sum({value_col}) AS total FROM {source} GROUP BY {group_col}",
        "sort": f"SELECT * FROM {source} ORDER BY {value_col} DESC LIMIT 1000",
        "join": (
            f"WITH totals AS (SELECT {group_col} AS k, sum({value_col}) AS total FROM {source} GROUP BY {group_col}) "
            f"SELECT count(*) AS n FROM {source} t LEFT JOIN totals USING (k)"
        ),
    }
    return aggregations[workload]


def polars_frame(workload: str, data: str, group_col: str, value_col: str):
    """Build the LazyFrame expression for a workload.

    Args:
        workload: One of WORKLOADS.
        data: Parquet path or glob.
        group_col: Grouping/key column.
        value_col: Numeric value column.

    Returns:
        A LazyFrame that is ready to collect.
    """
    import polars as pl  # pyrefly: ignore[missing-import]

    frame = pl.scan_parquet(data)
    if workload == "scan_agg":
        return frame.select(pl.col(value_col).sum().alias("total"))
    if workload == "filter_agg":
        return frame.filter(pl.col(value_col) > 0).select(pl.len().alias("n"))
    if workload == "groupby":
        return frame.group_by(group_col).agg(pl.col(value_col).sum().alias("total"))
    if workload == "sort":
        return frame.sort(value_col, descending=True).head(1000)
    totals = frame.group_by(group_col).agg(pl.col(value_col).sum())
    return frame.join(totals, on=group_col, how="left").select(pl.len().alias("n"))


def single_run(args: argparse.Namespace) -> int:
    """Execute one timed run in this process and print a JSON record.

    Args:
        args: Parsed arguments; expects engine and workload settings.

    Returns:
        Process exit status; 3 when the engine is not installed.
    """
    try:
        if args.engine == "polars":
            import polars as pl  # pyrefly: ignore[missing-import]

            version = pl.__version__
            query = polars_frame(args.workload, args.data, args.group_col, args.value_col)
            start = time.perf_counter()
            result = query.collect()
            elapsed = time.perf_counter() - start
            rows = result.height
        else:
            import duckdb  # pyrefly: ignore[missing-import]

            version = duckdb.__version__
            connection = duckdb.connect()
            if args.duckdb_memory_limit:
                connection.execute(f"SET memory_limit = '{args.duckdb_memory_limit}'")
            statement = duckdb_sql(args.workload, args.data, args.group_col, args.value_col)
            start = time.perf_counter()
            rows = len(connection.execute(statement).fetchall())
            elapsed = time.perf_counter() - start
            connection.close()
    except ImportError as error:
        print(json.dumps({"error": f"{error.name} is not installed"}))
        return 3
    except Exception as error:  # engine failures are data, not crashes
        print(json.dumps({"error": f"{type(error).__name__}: {error}"}))
        return 4
    print(
        json.dumps(
            {
                "engine": args.engine,
                "version": version,
                "seconds": elapsed,
                "rows": rows,
                "peak_rss_mb": peak_rss_mb(),
            },
        ),
    )
    return 0


def invoke_child(args: argparse.Namespace, engine: str) -> dict:
    """Run one child process for an engine.

    Args:
        args: Parent arguments.
        engine: `polars` or `duckdb`.

    Returns:
        Parsed child record, or a record with an `error` key.
    """
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--single-run",
        "--engine",
        engine,
        "--workload",
        args.workload,
        "--data",
        args.data,
        "--group-col",
        args.group_col,
        "--value-col",
        args.value_col,
    ]
    if args.duckdb_memory_limit:
        command += ["--duckdb-memory-limit", args.duckdb_memory_limit]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    try:
        record = json.loads(completed.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        record = {"engine": engine, "error": completed.stderr.strip() or f"child exited {completed.returncode}"}
    return record


def summarize(records: list[dict]) -> dict:
    """Aggregate successful runs into median seconds, peak RSS, and CV.

    Args:
        records: Child records for one engine.

    Returns:
        Summary dict with `ok`, `runs`, `median_seconds`, `peak_rss_mb`, `cv`.
    """
    failures = [record for record in records if "error" in record]
    runs = [record for record in records if "error" not in record]
    if not runs:
        return {"ok": False, "error": failures[-1]["error"] if failures else "no runs", "version": None}
    seconds = [record["seconds"] for record in runs]
    mean = statistics.fmean(seconds)
    deviation = statistics.stdev(seconds) if len(seconds) > 1 else 0.0
    return {
        "ok": True,
        "version": runs[0]["version"],
        "runs": len(runs),
        "median_seconds": statistics.median(seconds),
        "mean_seconds": mean,
        "cv": deviation / mean if mean else 0.0,
        "peak_rss_mb": max(record["peak_rss_mb"] for record in runs),
    }


def pick_winner(ratio: float) -> str:
    """Classify a polars/duckdb ratio as a win for either engine or a tie.

    Args:
        ratio: polars value divided by duckdb value.

    Returns:
        `polars`, `duckdb`, or `tie`.
    """
    if 1 / TIE_RATIO <= ratio <= TIE_RATIO:
        return "tie"
    return "polars" if ratio < 1 else "duckdb"


def verdict(polars: dict, duckdb: dict) -> str:
    """Compare two summaries into a human-readable verdict.

    Args:
        polars: Polars summary.
        duckdb: DuckDB summary.

    Returns:
        Verdict sentence.
    """
    if not polars["ok"] or not duckdb["ok"]:
        failed = [(name, summary) for name, summary in (("polars", polars), ("duckdb", duckdb)) if not summary["ok"]]
        details = "; ".join(f"{name}: {summary['error']}" for name, summary in failed)
        names = " and ".join(name for name, _summary in failed)
        return f"incomplete: {names} failed ({details})"
    time_ratio = polars["median_seconds"] / duckdb["median_seconds"]
    memory_ratio = polars["peak_rss_mb"] / duckdb["peak_rss_mb"] if duckdb["peak_rss_mb"] else 1.0
    time_winner = pick_winner(time_ratio)
    memory_winner = pick_winner(memory_ratio)
    noisy = max(polars["cv"], duckdb["cv"]) > 0.10
    note = " (high variance: treat as inconclusive)" if noisy else ""
    return f"time: {time_winner} ({time_ratio:.2f}x), memory: {memory_winner} ({memory_ratio:.2f}x){note}"


def print_table(polars: dict, duckdb: dict) -> None:
    """Print a compact comparison table.

    Args:
        polars: Polars summary.
        duckdb: DuckDB summary.

    Returns:
        None.
    """
    header = f"{'engine':<8} {'version':<12} {'runs':>4} {'median_s':>10} {'cv':>7} {'peak_rss_mb':>12}"
    print(header)
    print("-" * len(header))
    for name, summary in (("polars", polars), ("duckdb", duckdb)):
        if summary["ok"]:
            print(
                f"{name:<8} {str(summary['version']):<12} {summary['runs']:>4} "
                f"{summary['median_seconds']:>10.3f} {summary['cv']:>7.1%} {summary['peak_rss_mb']:>12.1f}"
            )
        else:
            print(f"{name:<8} {'-':<12} {'-':>4} failed: {summary['error']}")


def main() -> int:
    """Run the benchmark orchestration.

    Args:
        None.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Parquet file or glob readable by both engines")
    parser.add_argument("--workload", choices=WORKLOADS, default="groupby")
    parser.add_argument("--group-col", default="group")
    parser.add_argument("--value-col", default="value")
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--duckdb-memory-limit", help="e.g. 2GB; passed to SET memory_limit")
    parser.add_argument("--json", dest="json_path", help="write the full result JSON here")
    parser.add_argument("--engine", choices=["polars", "duckdb"], help=argparse.SUPPRESS)
    parser.add_argument("--single-run", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.single_run:
        return single_run(args)
    if args.repeat < 1 or args.warmup < 0:
        print("--repeat must be >= 1 and --warmup >= 0", file=sys.stderr)
        return 2
    if not glob.glob(args.data):
        print(f"no Parquet input matches: {args.data}", file=sys.stderr)
        return 2

    results: dict[str, list[dict]] = {"polars": [], "duckdb": []}
    for engine in ("polars", "duckdb"):
        for _ in range(args.warmup):
            invoke_child(args, engine)
        for _ in range(args.repeat):
            results[engine].append(invoke_child(args, engine))

    summaries = {engine: summarize(records) for engine, records in results.items()}
    print_table(summaries["polars"], summaries["duckdb"])
    outcome = verdict(summaries["polars"], summaries["duckdb"])
    print(f"\nverdict: {outcome}")

    if args.json_path:
        payload = {
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "cpu_count": os.cpu_count(),
                "data": args.data,
                "workload": args.workload,
                "repeat": args.repeat,
                "warmup": args.warmup,
                "duckdb_memory_limit": args.duckdb_memory_limit,
            },
            "engines": summaries,
            "verdict": outcome,
        }
        Path(args.json_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"wrote {args.json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
