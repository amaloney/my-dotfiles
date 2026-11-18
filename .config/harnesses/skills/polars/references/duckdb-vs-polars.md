# DuckDB vs Polars: conditional decision matrix

Verdicts are conditional. Both engines are vectorized, columnar, multi-threaded, in-process, and read the same
Parquet/CSV files. Published results disagree in both directions because scale, available memory, core count,
storage (local vs S3), and version dominate. Do not pick a winner from a headline number.

## Evidence base

| Study | Scale / setup | Result |
| --- | --- | --- |
| Polars PDS-H, May 2025 (vendor) | AWS c7a.24xlarge, 192 GB, local | SF-10: polars[streaming] 3.89 s vs duckdb 5.87 s vs polars[in-memory] 9.68 s. SF-100: streaming and DuckDB similar; Polars ahead except Q21 (range join falls back to in-memory) |
| pola.rs benchmark page (vendor, Polars 2.0) | 16 vCPU / 32 GB, then 192 vCPU | Polars faster on every PDS-H query; 1.77x at SF-100 on 192 vCPU |
| Coiled TPC-H (independent) | 10 GB local, 100 GB cloud | Polars excellent at 10 GB local; at 100 GB+ DuckDB more mature, Polars struggles with multi-table joins and cloud readers; Polars failures are hard (machine grinds) |
| codecentric (independent, excerpt-only) | 9 GB CSV, M1 Max 32 GB, cold/hot, 10 runs | DuckDB lowest peak memory (queries files without materializing); Polars ~100 MB behind after fixes; execution time close |
| Confessions of a Data Guy (independent, excerpt-only) | 1 TB Parquet on S3, 64 GB instance | DuckDB finished in 19 min with `memory_limit=54GB`; Polars OOM regardless of lazy mode |
| Miles Cole LakeBench (independent) | 10 GB, 2/4/8 vCPU | 2 vCPU: Polars fastest; 4 vCPU: DuckDB wins; 8 vCPU: DuckDB slightly ahead |
| DuckDB engineering | engine design | Streaming execution always on; spills group-by/join/sort/window intermediates to disk under `memory_limit`; buffer manager caches pages (Raasveldt 2024; SIGMOD 2019) |

## Matrix

Choose **DuckDB** when any of these hold:

| Condition | Why | Source |
| --- | --- | --- |
| Data or blocking-operator intermediates exceed RAM, and the job must complete | `memory_limit` + `temp_directory` spill group-by, join, sort, window; Polars may have no completing path | DuckDB memory blog; DuckDB tuning docs; 1 TB test |
| Strict memory ceiling on a shared/commodity box | memory cap is explicit and enforced, default 80% RAM | DuckDB memory blog |
| 100 GB+ with many multi-table joins | DuckDB join ordering + maturity; Polars documented struggles | Coiled TPC-H |
| Files on S3/HDFS with a slow or unreliable network and limited RAM | async I/O, filters/projection pushdown, external file cache, never materializes the table | DuckDB tuning docs; codecentric |
| Ingest/export larger than memory (CSV <-> Parquet) | `preserve_insertion_order=false` cuts memory | DuckDB tuning docs |
| SQL is the native language of the task, or the task is many small parameterized queries | prepared statements, connection reuse | DuckDB tuning docs |
| Core count is moderate (4-8 vCPU) and data is ~10 GB | independent benchmark shows DuckDB ahead there | Miles Cole |

Choose **Polars** when any of these hold:

| Condition | Why | Source |
| --- | --- | --- |
| Data fits in RAM with headroom, single node | in-memory engine and streaming engine are competitive to dominant | Polars PDS-H; pola.rs benchmarks |
| Workload is expression-heavy transforms (strings, dates, lists, structs), not SQL-shaped | expression API breadth, per-core speed | Official Polars skill; pola.rs benchmarks |
| Very low core count (2 vCPU) at ~10 GB | Polars won that configuration | Miles Cole |
| The pipeline is DataFrame-shaped and ends in Python objects / Arrow interchange | avoids SQL string plumbing | Coiled (subjective); Official Polars skill |
| You need fine-grained streaming control via sinks (`sink_parquet` partitioning) | first-class sink API | Polars: Sources and sinks |

## Decision procedure (ordered, deterministic)

1. Estimate peak working set: input size plus the largest blocking operator (group-by cardinality, join build side,
   sort). If `working_set > 0.6 * available_ram`, prefer DuckDB, or prove Polars streaming covers every operator
   (`explain(engine="streaming")`).
2. If data is remote (S3/HTTP) and RAM is constrained, prefer DuckDB.
3. If the job is SQL-shaped or multi-table joins at 100 GB+, prefer DuckDB.
4. If data fits in RAM and the task is DataFrame/expression-shaped, prefer Polars.
5. If steps 1-4 conflict, or the margin is under 2x, do not guess: run `scripts/bench_engines.py` on the actual
   data and hardware and record the environment with the result. The sources themselves say results are
   hardware/workload specific; measurement is the only tiebreaker.

## What the research recommends for the skill

- Static decision matrix is the primary mechanism: the conditions above are stable engine properties (spilling,
  memory cap, async remote I/O) and are unlikely to invert.
- A benchmark script is warranted for disputes and for memory-tight jobs, because independent benchmarks
  contradict vendor benchmarks in both directions. Hence `scripts/bench_engines.py`.
- Never auto-rewrite a Polars pipeline into SQL. The engines are not general-purpose interchangeable; the script
  compares a workload, it does not translate code.

## Caveats

- Vendor benchmarks use very large core counts and generous RAM; independent ones use small cloud instances. Your
  laptop is closer to the independent setups.
- DuckDB's spill advantage disappears when the query has multiple blocking operators; it can still OOM (DuckDB
  tuning docs, "Limitations").
- Polars' streaming engine changes quickly; re-verify version-specific claims (Polars 2.0 rewrote it).
- The 1 TB and codecentric results are excerpt-only captures (bot-blocked). Treat them as directional.
