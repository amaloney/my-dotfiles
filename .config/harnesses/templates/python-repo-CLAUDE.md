# Project Instructions

## Session Start

1. Check `.claude/code_index/profile.json` exists and fresh (<7 days)
2. If missing/stale → run [[python/recon]] to generate profile
3. Load [[python]] orchestrator
4. Read `README.md` and `TODO.md` (if exists) for context

```bash
# Check profile status
test -f .claude/code_index/profile.json && \
  find .claude/code_index/profile.json -mtime -7 | grep -q . && \
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
cat .claude/code_index/profile.json | jq '.project.type'
cat .claude/code_index/profile.json | jq '.patterns.config_py_path'
```

## Python Workflow

| Task           | Load                                                          |
| -------------- | ------------------------------------------------------------- |
| New code       | [[python/style]] → [[python/violations]] → [[python/bugs]]    |
| Tests          | [[python/testing]] + [[python/conftest]] + [[python/mocking]] |
| Property tests | [[python/property-testing]]                                   |
| Bug fix        | [[python/bugs]] → verify with test                            |
| Security       | [[python/security]]                                           |
| Refresh profile| [[python/recon]]                                              |

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
