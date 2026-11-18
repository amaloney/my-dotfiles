# Gate rules: evidence, detection, confidence

`scripts/polars_gates.py` implements these rules. Every rule below survived the static-checkability screen: it is an
AST-detectable pattern with a documented reason. Rules that need runtime context (data size, memory headroom, column
cardinality) are **not** gates; they live in [duckdb-vs-polars.md](duckdb-vs-polars.md) and
[polars-memory.md](polars-memory.md).

Severity: `error` blocks (hook exits 2); `hint` informs (listed, does not block).

| Code | Severity | Pattern | Why | Evidence |
| --- | --- | --- | --- | --- |
| POL001 | error | `pl.read_csv/read_parquet/read_json/read_ndjson/read_ipc` in a Polars file | eager read materializes before the optimizer runs; `scan_*` enables predicate/projection pushdown and streaming | Polars: Sources and sinks; Official Polars skill |
| POL002 | error | `.map_elements(`, `.apply(`, `.map_groups(` | per-value Python call, disables optimizer, emits `PolarsInefficientMapWarning` | Polars: UDFs; Official Polars skill |
| POL003 | hint | `.map_batches(` | one Python call per Series; fine for compiled ufuncs, slow otherwise | Polars: UDFs |
| POL004 | error | `.iter_rows(` | row-wise Python iteration; the expression API covers nearly all uses | Official Polars skill |
| POL005 | hint | `.to_pandas()` in a Polars file | copies out of Arrow; needed only at library boundaries | Official Polars skill (lazy-first stance) |
| POL006 | hint | pandas `read_*` in a Polars file | reads through pandas then converts; prefer `scan_*` | Official Polars skill |
| POL007 | error | `.collect().<op>(` chained | collect mid-chain materializes and discards the plan; later ops re-optimize | Official Polars skill ("collect exactly once") |
| POL008 | hint | list comprehension passed to `select`/`with_columns`/`agg` | per-column expressions serialize; one expanded expression runs in parallel | Official Polars skill |
| POL009 | error | `.groupby(`, `.iloc[` in a Polars file | pandas spellings; wrong/absent API in Polars (`iterrows` is POL004) | Official Polars skill (pandas traps) |
| POL010 | error | `warnings.filterwarnings("ignore")`, `warnings.simplefilter("ignore")` in a Polars file | suppresses the warning that names the performance fix | Official Polars skill |

## Not gated (documented instead)

| Pattern | Why no gate |
| --- | --- |
| `.collect()` without `engine="streaming"` | correct when data fits in RAM; Polars 2.0 may already default to streaming. Runtime data size decides |
| `read_parquet` inside a one-shot script on a small file | POL001 covers the common case; a gate cannot weigh intent |
| `Categorical` vs `Enum` | needs cardinality knowledge; see memory reference |
| join order / filter placement | optimizer handles most cases; needs a plan, not an AST |
| `multiprocessing` around Polars | real hazard (thread oversubscription), but not verified against current docs in this research pass |

## Suppression

- Line: `x = df.iter_rows()  # polars-gate: allow POL004`
- File: first line `# polars-gate: allow-file POL001, POL003`
- Suppressions are counted in `--json` output (`suppressed`) so they stay auditable.

## Confidence tiers

| Tier | Rules | Basis |
| --- | --- | --- |
| High (gate) | POL001, POL002, POL004, POL007, POL009, POL010 | Explicit in official docs or the official Polars skill |
| Medium (hint) | POL003, POL005, POL006, POL008 | Documented cost, legitimate exceptions |

New rules require a reference citation and a fixture pair (failing + passing), otherwise they stay prose.
