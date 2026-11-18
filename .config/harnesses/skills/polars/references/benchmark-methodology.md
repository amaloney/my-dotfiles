# Benchmark methodology

Sources: Polars PDS-H results, Coiled TPC-H, codecentric benchmark, DuckDB tuning docs, official Polars skill.
Independent and vendor results differ, so the method matters as much as the number.

## Rules

1. **Pin versions.** Record `polars.__version__`, `duckdb.__version__`, Python, OS, CPU, RAM. Engine rewrites change
   results across minor versions.
2. **Pin the data.** Same Parquet files, same compression, local disk unless remote I/O is the question.
3. **Equivalent work.** Same filters, same aggregations, same output columns. SQL `SELECT *` and a Polars
   `select(pl.all())` are both wrong for timing projection-sensitive queries.
4. **Warmup run, then N >= 5 measured runs.** Report median and coefficient of variation; discard the warmup.
   OS page cache and DuckDB's buffer manager both make run 1 unrepresentative.
5. **Measure peak RSS, not just time.** The decision matrix turns on memory. Peak RSS distinguishes "fast because it
   materialized everything" from "fast and frugal".
6. **Separate cold and hot runs** when I/O is part of the question. Do not claim cold-cache numbers without flushing
   or isolating the cache; macOS does not expose a full page-cache flush.
7. **Do not mix engines in one process for timing.** Import/teardown, allocator state, and thread pools interact;
   run each engine in its own subprocess.
8. **State the machine's core count.** Polars and DuckDB both parallelize; a 2-vCPU result does not transfer to
   96 vCPUs. Miles Cole's LakeBench flips winner between 2 and 4 vCPU.
9. **Report negative results.** If Polars OOMs or falls back to in-memory, that is the result.
10. **Do not compare vendor headline numbers with your own.** Re-run on your hardware.

## What `scripts/bench_engines.py` implements

- One Parquet input (or glob), one built-in workload (`groupby`, `join`, `sort`, `filter_agg`, `scan_agg`).
- Each engine in a fresh subprocess; wall time and peak RSS collected per run.
- Warmup (`--warmup 1`) then `--repeat 5`; median and coefficient of variation printed.
- Optional `--duckdb-memory-limit` to reproduce a constrained-memory scenario.
- Output: table plus a verdict (faster / lower memory / tie), JSON with `--json`.
- Exit code 0 on a completed comparison regardless of verdict; 2 for bad arguments or a missing input. A missing
  engine is reported as an incomplete verdict with its import error. A verdict is evidence, not a gate.

## Interpreting a verdict

- Time difference under 10% with CV over 10%: treat as tie; increase repeats or fix the noise source.
- Memory difference matters when the losing engine's peak approaches the machine limit; that is when the
  larger-than-memory conditions in [duckdb-vs-polars.md](duckdb-vs-polars.md) apply.
- If both engines OOM, the workload needs partitioning or a distributed engine, not a different local engine.
