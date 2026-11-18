# Polars memory patterns

## Where memory goes

- Default (in-memory) `collect` processes the whole dataset as one batch; peak memory must cover the query
  (Polars: Query execution).
- Streaming processes batches, so a small-group aggregation or a scan-to-sink pipeline can run larger than memory.
  Operations that must buffer everything (large-cardinality group-by, sort, large joins, complex windows) remain
  memory-heavy and may fall back to the in-memory engine (Polars: Streaming).
- Python UDFs copy Series into NumPy arrays; `map_batches` on a full Series can double peak memory for that column
  (Polars: UDFs).

## Levers

| Lever | Effect | Source |
| --- | --- | --- |
| `scan_*` instead of `read_*` | avoid full materialization before the query plan runs | Polars: Sources and sinks |
| `collect(engine="streaming")` (1.x) | batch execution, larger-than-memory where supported | Polars: Streaming |
| `sink_parquet` / `sink_csv` / `sink_ndjson` | stream results to disk instead of materializing | Polars: Sources and sinks |
| `pl.collect_all` on shared base | computes shared subplans once instead of per query | Official Polars skill |
| single `.collect()` | each intermediate collect holds a full materialization | Official Polars skill |
| `Enum` / `Categorical` for repeated strings | integer codes instead of per-row strings | Polars: Categoricals |
| smaller `physical` type in `pl.Categories` | `UInt8`/`UInt16` codes when category count is small | Polars: Categoricals |
| `is_elementwise=True` on `map_batches` | avoids handing the whole Series to the callable | Polars: UDFs |

Polars has no documented global memory limit / spill-to-disk setting comparable to DuckDB's `memory_limit` +
`temp_directory`; the streaming engine is the documented out-of-core mechanism, with per-operator coverage limits
(Polars: Streaming; DuckDB: Memory Management for the contrast).

## Known failure shape

Independent 1 TB S3/Parquet tests report Polars OOM under a 64 GB instance with no way to cap memory, while DuckDB
completed with `memory_limit=54GB` and disk spilling (Confessions of a Data Guy, excerpt-only). Treat any
"much larger than RAM" job on Polars as unproven until measured on the target hardware: see
[duckdb-vs-polars.md](duckdb-vs-polars.md).

## Version notes

- Streaming engine was rewritten across 1.x -> 2.0; older OOM reports may not reproduce. Re-test before concluding.
- The docs list streaming coverage per operator; `explain(engine="streaming")` / `show_graph(plan_stage="physical",
  engine="streaming")` reveals fallbacks (Polars: Streaming).
