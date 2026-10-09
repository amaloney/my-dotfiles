---
name: code-index
description:
  Semantic search of the current codebase via ChromaDB + bi-temporal AST knowledge graph. MUST run before any new code
  is written — returns file:symbol references for similar existing code, or an explicit no-match verdict that justifies
  greenfield creation.
invocation: manual
---

# Code Index

Handoff: `next: done`.

Bi-temporal code knowledge graph + semantic search. ChromaDB stores entity embeddings; SQLite stores entities, relations
(calls/inherits/imports), and git-tracked temporal history.

Per the handoff contract: this skill is the energy barrier. New code requires an explicit no-match verdict from here
first.

## Setup (once per repo)

```bash
~/.config/harnesses/skills/code-index/scripts/install.sh .   # installs to .harness/code_index/
pixi install -e dev                                          # dev env from pyproject.toml below
pixi run -e dev index                                        # build index
```

Index deps live in a pixi `dev` feature in `pyproject.toml` ([[python/pixi-pyproject]]). The startup hook
(`harness-refresh.sh`) uses `.pixi/envs/dev/bin/python`, then `.pixi/envs/default/bin/python`, then system `python3`.

```toml
[tool.pixi.feature.dev.dependencies]
chromadb = ">=1.5"
# pkgs/main build sets the executable-stack flag, which glibc >= 2.41 refuses to load
onnxruntime = { version = "*", channel = "conda-forge" }
tree_sitter = ">=0.24"                                       # Rust repos only
tree-sitter-rust = ">=0.24"                                  # Rust repos only

[tool.pixi.environments]
default = { solve-group = "default" }
dev = { features = ["dev"], solve-group = "default" }

[tool.pixi.feature.dev.tasks]
index = { cmd = "python build_index_temporal.py", cwd = ".harness/code_index" }
query = { cmd = "python query_temporal.py", cwd = ".harness/code_index" }
```

Languages: Python via `ast`; Rust via tree-sitter (`extract_rust.py` — structs/enums/traits as `class`, impl/trait fns
as `method`, `impl Trait for Type` as `inherits`). Without tree-sitter-rust installed, `.rs` files are skipped with one
warning. Cargo projects index the whole crate/workspace root, excluding `target/`.

Index instances are per-repo under `.harness/code_index/` (gitignore the whole dir). Re-run the builder after large
changes.

## Usage

Run from the repo root (scripts live at `.harness/code_index/`):

| Command                                                             | Purpose                              |
| ------------------------------------------------------------------- | ------------------------------------ |
| `python3 .harness/code_index/query_temporal.py search "<intent>"`   | Semantic search for similar entities |
| `python3 .harness/code_index/query_temporal.py callers <name>`      | Who calls this entity                |
| `python3 .harness/code_index/query_temporal.py calls <name>`        | What this entity calls               |
| `python3 .harness/code_index/query_temporal.py impact <name>`       | Change impact analysis               |
| `python3 .harness/code_index/query_temporal.py changes 7d`          | What changed recently                |

## Verdict protocol (output contract)

1. `search` with a query describing the requested behavior (not names — intent: "download PyPI JSON and cache to disc").
2. Inspect top results' similarity scores:
   - **score >= 0.8** → match. Return `file:symbol` refs only (e.g. `src/net/fetch.py:get_json`), verdict: `similar`.
   - **below** → verdict: `no match`.
3. Never paste code bodies into the result. References only; downstream agents read from disc.

Result format (one short message):

```
verdict: similar | no-match
refs: file:symbol (score), file:symbol (score)
```

## Flywheel (pattern learning)

`flywheel.py` tracks fix outcomes as Beta distributions and promotes proven patterns / flags anti-patterns. Query before
fixing familiar error classes:

```bash
python3 .harness/code_index/flywheel.py recommend <error_type>
python3 .harness/code_index/flywheel.py skills --bayesian
```

Full theory and CLI reference: `scripts/README.md` (relative to this skill dir).
