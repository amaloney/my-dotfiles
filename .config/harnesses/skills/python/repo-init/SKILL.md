---
name: python/repo-init
description: Bootstrap Python repo instructions, profile, and project recon
---

# Python Repo Init

Handoff: `next: done`.

Bootstrap harness integration for a Python repo: repo-level instructions + `.harness/` profile.

## When

User asks to set up / onboard / initialize a Python project for harness-assisted work, or a Python repo lacks
`AGENTS.md` / `.harness/code_index/profile.json`.

## Steps

1. Write the repo instructions below to `<repo>/AGENTS.md`. If one exists, merge — never overwrite silently.
2. Run project recon (see below) to generate `.harness/code_index/profile.json`.
3. Ensure `.harness/` is in the repo's `.gitignore` (generated state, never committed).
4. Offer the code index: `~/.config/harnesses/skills/code-index/scripts/install.sh <repo>`.

## Project Recon

Run FIRST before other Python skills. Outputs `.harness/code_index/profile.json`.

**When to run:** Session start in Python repo, after major refactor, or when profile.json missing/stale (>7 days).

```bash
~/.config/harnesses/skills/python/recon/scripts/profile.sh
```

Review/fill `.harness/code_index/profile.json`: the script populates version, generated, and project fields; fill
structure, patterns, testing, and linting from the scan results.

**Staleness check:**

```bash
find .harness/code_index/profile.json -mtime +7 2>/dev/null && echo "stale"
```

Skills read profile.json instead of rescanning: constants should be in `{profile.patterns.config_py_path}`.

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

| Task            | Load                                              |
| --------------- | ------------------------------------------------- |
| New code        | python/style → debugging                          |
| Tests           | python/testing + python/conftest + python/mocking |
| Property tests  | python/property-testing                           |
| Bug fix         | debugging → verify with test                      |
| Security        | python/security                                   |
| Refresh profile | python/recon                                      |

## Rules (from profile)

- Constants → `profile.patterns.config_py_path` (NEVER mid-file)
- Tests → `profile.structure.test_dirs`
- Lint with → `profile.linting.tool`

## Testing

```bash
conda run -n proj pytest tests/path/test_specific.py -x
```

## Tools

```bash
conda run -n proj ruff check .
conda run -n proj ruff format .
conda run -n proj pytest
```
````

[[python]] [[python/structure]]
