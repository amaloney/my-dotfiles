# Polars performance patterns

Evidence for each claim is the source in parentheses; see [index.md](index.md) for URLs.

## Use the lazy API end to end

- `scan_*` beats `read_*`: scans are lazy, let the optimizer push projections/predicates into the reader, and let
  streaming start before the file is fully read (Polars: Sources and sinks).
- Start from `.lazy()` even when data is already a DataFrame: `.lazy()` wraps without copying and turns step-by-step
  eager calls into one optimized plan (Official Polars skill; Polars: Optimizations).
- One `.collect()` per query, at the end. Each collect materializes and discards the plan; everything after it
  re-optimizes from scratch (Official Polars skill).
- Diverging queries: build from one base `LazyFrame` and execute with `pl.collect_all` so shared subplans run once
  (Polars: Query execution; Official Polars skill).

Optimizer passes that make laziness pay: predicate pushdown, projection pushdown, slice pushdown, common subplan
elimination, expression simplification, join ordering, type coercion, cardinality estimation (Polars: Optimizations).

## Native expressions over Python callables

- `map_elements` calls Python once per value; the docs call this out as slow and it disables the optimizer (Polars:
  UDFs). Polars emits `PolarsInefficientMapWarning` for the common cases.
- `map_batches` is one Python call per Series/group; acceptable when the callable is a compiled ufunc (`numpy.log`,
  Numba `@guvectorize`), otherwise still an interpreter loop (Polars: UDFs).
- Never hide the warnings: `warnings.filterwarnings("ignore")` / `catch_warnings` suppress the exact signal that names
  the fix (Official Polars skill).
- Row-level Python loops (`iter_rows`, `to_dicts` then loop) are the slowest shape; the expression API covers
  almost all of it (Official Polars skill).

## Reduce work before it reaches the next operator

- Filter before `group_by`, `join`, `with_columns` so every later step sees less data (Official Polars skill).
- Pass all expressions to one `with_columns`/`select` context: expressions in one context run in parallel; repeated
  calls serialize (Official Polars skill).
- Expand one expression over columns (`pl.col("a", "b")`, `cs.numeric()`, `.name.suffix`) instead of a Python list
  comprehension of per-column expressions (Official Polars skill).
- Handle dirty data at the scan (`null_values`, `try_parse_dates`, `schema_overrides`) so downstream casts and
  fallbacks do not dominate (Official Polars skill).

## Cardinality and types

- `Enum` is faster than `Categorical`: fixed mapping, no re-encoding, no global-mapping lock; use `Categorical` only
  when categories are unknown or grow (Polars: Categorical data and enums).
- Repeated strings compared/joined as plain `String` pay repeated string comparison and memory for every row;
  encoding to `Enum`/`Categorical` stores integers (Polars: Categorical data and enums).
- Strict typing means explicit casts are required; the optimizer can only work on known dtypes (Official Polars
  skill).

## Version notes

- Polars 2.0: the official skill states `.collect()` runs on the streaming engine by default and that `engine="streaming"`
  is the larger-than-memory switch on 1.x. Check `pl.__version__` before relying on either default.
- Streaming coverage is incomplete for some operators; an unsupported operator falls back to the in-memory engine
  (Polars: Streaming), and a range join in PDS-H Q21 was the documented fallback in the May 2025 benchmark
  (Polars: PDS-H results).
