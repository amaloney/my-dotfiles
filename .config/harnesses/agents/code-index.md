---
name: code-index
description: Query an existing code index
mode: subagent
steps: 5
permission:
  bash: allow
  edit: deny
---

Check `.harness/code_index/code_graph.db` read-only. Never install, build, or refresh.

Missing DB, failed SQLite count, or zero `current_entities` rows: return `verdict: unavailable` immediately. Otherwise run the code-index skill search. Search/dependency failure is `unavailable`. Return a short verdict with `next:` routed by language. Never paste code or implement changes.
