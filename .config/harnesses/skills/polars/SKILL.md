---
name: polars
description: Optimize Polars analysis for speed and memory, and decide when DuckDB wins. Use when writing, reviewing, or debugging Polars code, choosing between Polars and DuckDB, or handling larger-than-memory tabular workloads.
invocation: auto
extensions: [".py", ".ipynb"]
keywords: ["polars", "lazyframe", "duckdb", "dataframe", "parquet", "larger than memory", "arrow"]
---

# Polars optimization

Handoff: `next: verify`.

Default stance: lazy API end to end, one `collect()`, native expressions, filter early. The hook enforces the
statically checkable rules; the references carry everything that needs judgment.

## Deterministic enforcement

`scripts/polars_gates.py` runs on every edit to a Python file that imports Polars (Claude PostToolUse hook, Kilo
`polars-gates.js` plugin). The hook blocks on `error` rules; `hint` rules surface in CLI runs.

```bash
polars_gates.py analysis.py --json          # CLI: exit 1 on findings
polars_gates.py --event edit                # hook mode: JSON on stdin, exit 2 on errors
polars_gates.py --explain POL002            # why a rule exists
```

| Code | Severity | Fix |
| --- | --- | --- |
| POL001 | error | `read_*` -> `scan_*` |
| POL002 | error | `map_elements`/`apply`/`map_groups` -> native expression |
| POL003 | hint | `map_batches` only for compiled ufuncs |
| POL004 | error | `iter_rows` -> expression |
| POL005 | hint | `to_pandas` only at a library boundary |
| POL006 | hint | pandas reader -> `scan_*` |
| POL007 | error | `.collect()` mid-chain -> collect once |
| POL008 | hint | comprehension of per-column expressions -> one expanded expression |
| POL009 | error | `groupby`/`iloc` are not Polars APIs (`iterrows` is POL004) |
| POL010 | error | never suppress Polars warnings; they name the fix |

Suppress intentional cases: `# polars-gate: allow POL001` or, on line 1, `# polars-gate: allow-file POL001`.
Full rationale and confidence tiers: [references/gate-rules.md](references/gate-rules.md).

## Canonical shape

```python
result = (
    pl.scan_parquet("events/*.parquet")
    .filter(pl.col("year") == 2026)
    .join(customers, on="customer_id", how="left")
    .with_columns((pl.col("revenue") - pl.col("cost")).alias("profit"))
    .group_by("region")
    .agg(pl.col("profit").sum().alias("total"))
    .sort("total", descending=True)
    .collect(engine="streaming")  # 1.x; Polars 2.0 may default to streaming
)
```

Polars exposes no documented global memory-limit or spill-directory setting comparable to DuckDB's; the streaming
engine is the documented out-of-core mechanism, and some operators fall back to in-memory. See
[references/polars-memory.md](references/polars-memory.md).

## Polars or DuckDB

Run the ordered decision procedure in [references/duckdb-vs-polars.md](references/duckdb-vs-polars.md). Short form:

1. Working set (input + largest blocking operator) over ~60% of RAM -> prefer DuckDB (explicit `memory_limit` +
   spill), or prove every operator streams via `explain(engine="streaming")`.
2. Remote data with constrained RAM -> DuckDB.
3. SQL-shaped work or multi-table joins at 100 GB+ -> DuckDB.
4. Data fits in RAM and work is expression-shaped -> Polars.
5. Conflict or under 2x margin -> measure, do not guess:

```bash
bench_engines.py --data events/*.parquet --workload groupby --group-col region --value-col amount --repeat 5
bench_engines.py --data data.parquet --workload sort --value-col ts --duckdb-memory-limit 2GB --json result.json
```

The verdict is evidence, not a rewrite order. Never auto-translate a Polars pipeline to SQL.

## References

- [references/index.md](references/index.md) - sources, saturation, maintenance
- [references/polars-performance.md](references/polars-performance.md) - lazy API, expressions, cardinality
- [references/polars-memory.md](references/polars-memory.md) - streaming, sinks, memory levers
- [references/duckdb-vs-polars.md](references/duckdb-vs-polars.md) - conditional decision matrix
- [references/benchmark-methodology.md](references/benchmark-methodology.md) - how to measure credibly
- [references/gate-rules.md](references/gate-rules.md) - rule evidence and confidence

## Maintenance

Re-verify version-sensitive claims when Polars or DuckDB majors change; the streaming engine and default collect
behavior have both changed across releases. Add sources to `references/index.md` first, then to the topic file.
