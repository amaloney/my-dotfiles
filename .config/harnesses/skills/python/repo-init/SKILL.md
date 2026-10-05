---
name: python/repo-init
description: Bootstrap repo-level AGENTS.md + .harness profile for a Python project
---

# Python Repo Init

Bootstrap harness integration for a Python repo: repo-level instructions + `.harness/` profile.

## When

User asks to set up / onboard / initialize a Python project for harness-assisted work, or a Python repo lacks
`AGENTS.md` / `.harness/code_index/profile.json`.

## Steps

1. Write the repo instructions below to `<repo>/AGENTS.md`. If one exists, merge — never overwrite silently.
2. Load [[python/recon]] and run it to generate `.harness/code_index/profile.json`.
3. Ensure `.harness/` is in the repo's `.gitignore` (generated state, never committed).
4. Offer the code index: `~/.config/harnesses/skills/code-index/scripts/install.sh <repo>`.

## Repo instructions (write to AGENTS.md)

````markdown
# Project Instructions

## Session Start

1. Check `.harness/code_index/profile.json` exists and fresh (<7 days)
2. If missing/stale → run python/recon to generate profile
3. Load the python orchestrator skill
4. Read `README.md` and `TODO.md` (if exists) for context

```bash
# Check profile status
test -f .harness/code_index/profile.json && \
  find .harness/code_index/profile.json -mtime -7 | grep -q . && \
  echo "CURRENT" || echo "NEEDS UPDATE"
```

## Profile (code_index/profile.json)

All skills read this instead of scanning. Contains:

- `project.type` — cli | library | webapp | datascience
- `structure.src_dirs` — where source code lives
- `patterns.config_py_path` — where constants should go
- `patterns.scattered_constants` — violations to fix
- `testing.framework` — pytest | unittest

```bash
# Quick queries
cat .harness/code_index/profile.json | jq '.project.type'
cat .harness/code_index/profile.json | jq '.patterns.config_py_path'
```

## Python Workflow

| Task            | Load                                                        |
| --------------- | ----------------------------------------------------------- |
| New code        | python/style → python/violations → debugging                |
| Tests           | python/testing + python/conftest + python/mocking           |
| Property tests  | python/property-testing                                     |
| Bug fix         | debugging → verify with test                                |
| Security        | python/security                                             |
| Refresh profile | python/recon                                                |

## Rules (from profile)

- Constants → `profile.patterns.config_py_path` (NEVER mid-file)
- Tests → `profile.structure.test_dirs`
- Lint with → `profile.linting.tool`

## Testing

```bash
# Targeted only — never full suite
pytest tests/path/test_specific.py -x
```

## Tools

```bash
ruff check .          # Lint
ruff format .         # Format
uv run pytest         # If using uv
pixi run test         # If using pixi
```
````

[[python]] [[python/recon]]
