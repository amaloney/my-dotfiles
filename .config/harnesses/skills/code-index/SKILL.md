---
name: code-index
description: Query an existing code index
invocation: manual
---

# Code Index

Handoff: `next: done`.

SQLite stores code entities and relations; ChromaDB stores semantic embeddings. The gate is read-only: never install, build, or refresh an index.

## Gate

1. Missing `.harness/code_index/code_graph.db` → `unavailable`.
2. Run `sqlite3 -readonly .harness/code_index/code_graph.db 'SELECT COUNT(*) FROM current_entities;'`. Query error or zero rows → `unavailable` immediately.
3. On a populated index, run `python3 .harness/code_index/query_temporal.py search "<requested behavior>"`. Search/dependency failure → `unavailable`; do not install anything.
4. Score >= 0.8 is a reuse match; otherwise return `no-match`.
5. Return only:

```
verdict: similar | no-match | unavailable
refs: file:symbol (score), ...
next: <stage>
```

Never paste code. `unavailable` is not a no-match; main may proceed on the explicit user request without rebuilding the index.

## Pre-Create Duplicate Check

Before creating a new function, class, or constant, query the index:

```bash
python3 .harness/code_index/query_temporal.py duplicates | grep -i "<name>"
```

If the name exists elsewhere:
- **Reuse**: Import and use the existing implementation
- **Refactor**: If existing is insufficient, modify it rather than creating parallel

The `find_duplicates()` command returns same-name entities in different files. High-similarity names (e.g.,
`fetch_metadata` vs `get_metadata`) warrant manual review via semantic search.

Build or refresh only in a separate main-agent action, following `scripts/README.md`.
