# Polars optimization research index

Research date: 2026-11-18. Raw captures live in `.harness/research/2026-11-18/` (regenerable, gitignored). This
directory is the durable, human-readable corpus.

## Topics

| File | Question | Verdict |
| --- | --- | --- |
| [polars-performance.md](polars-performance.md) | Which coding patterns measurably slow Polars down? | Lazy API, one collect, native expressions, filter early |
| [polars-memory.md](polars-memory.md) | Which patterns reduce/raise memory? | scan + streaming + sinks; Enum over Categorical |
| [duckdb-vs-polars.md](duckdb-vs-polars.md) | When does DuckDB win over Polars? | DuckDB wins under hard memory limits and larger-than-RAM joins; Polars wins in-RAM |
| [benchmark-methodology.md](benchmark-methodology.md) | How to measure credibly? | Warmup, repeats, median, peak RSS, pinned versions, report env |
| [gate-rules.md](gate-rules.md) | What is statically checkable? | POL001-POL010; evidence tier per rule |

## Sources

| Type | Source | URL |
| --- | --- | --- |
| Documentation | Polars: Optimizations | https://docs.pola.rs/user-guide/lazy/optimizations |
| Documentation | Polars: Streaming | https://docs.pola.rs/user-guide/concepts/streaming |
| Documentation | Polars: Sources and sinks | https://docs.pola.rs/user-guide/lazy/sources_sinks |
| Documentation | Polars: User-defined Python functions | https://docs.pola.rs/user-guide/expressions/user-defined-python-functions/ |
| Documentation | Polars: Categorical data and enums | https://docs.pola.rs/user-guide/expressions/categorical-data-and-enums/ |
| Code / skill | Official Polars agent skill (`polars-inc/skills`) | https://github.com/polars-inc/skills/blob/main/skills/polars/SKILL.md |
| Blog | Polars: PDS-H benchmark results (May 2025) | https://pola.rs/posts/benchmarks |
| Blog | Polars: benchmark landing page | https://pola.rs/benchmarks/ |
| Blog | Polars: a bird's eye view (engine design) | https://pola.rs/posts/polars_birds_eye_view/ |
| Blog | Coiled: DataFrames at Scale (TPC-H) | https://tpch.coiled.io/ |
| Blog | codecentric: DuckDB vs Polars vs Pandas benchmark | https://www.codecentric.de/en/knowledge-hub/blog/duckdb-vs-dataframe-libraries |
| Blog | Confessions of a Data Guy: 1 TB DuckDB vs Polars | https://www.confessionsofadataguy.com/duckdb-beats-polars-for-1tb-of-data |
| Blog | Miles Cole: Spark vs DuckDB vs Polars (LakeBench) | https://milescole.dev/data-engineering/2024/12/12/Should-You-Ditch-Spark-DuckDB-Polars.html |
| Blog | DuckDB: Memory Management in DuckDB (2024-07-09) | https://duckdb.org/2024/07/09/memory-management |
| Documentation | DuckDB: Tuning Workloads (2.0) | https://duckdb.org/docs/2.0/guides/performance/how_to_tune_workloads.html |
| Paper | Raasveldt & Mühleisen, "DuckDB: An Embeddable Analytical Database", SIGMOD 2019 | https://doi.org/10.1145/3299869.3320212 |

Two sources could not be captured automatically (bot protection, HTTP 403/406 on 2026-11-18); they are cited from
search-result excerpts only and are marked `excerpt-only` where used: codecentric benchmark, Confessions 1 TB post.

Papers: DuckDB has a peer-reviewed design paper (SIGMOD 2019). No peer-reviewed paper on the Polars engine was found;
the closest design description is the Polars "bird's eye view" blog (https://pola.rs/posts/polars_birds_eye_view/),
which is not captured here, so no Polars paper is cited rather than a guessed one.

## Saturation

Stopped when new searches repeated the same six primary sources (Polars docs, official Polars skill, Polars PDS-H,
Coiled TPC-H, DuckDB docs/blog, independent blog benchmarks). Vendor and independent results disagree on direction
at 100 GB scale; this is recorded as a conditional verdict rather than resolved.

## Maintenance

- Re-verify version-sensitive claims when Polars or DuckDB majors change; `polars-performance.md` and `polars-memory.md`
  carry version notes.
- Add new sources as rows above and a line in the topic file; never edit a capture in place.
- Re-run `scripts/bench_engines.py` on your own hardware before trusting either vendor's headline number.
