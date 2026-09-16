# Project Instructions

## Session Start

1. Load [[python]] orchestrator before any code work
2. Check `.claude/code_index/` — if missing/stale, offer to create/update
3. Query code_index for context before exploring manually

## Code Index

Index must include:

- All `.py` files (functions, classes, imports)
- `README.md` — project context, setup, architecture
- `TODO.md` — current tasks, priorities (if exists)
- `pyproject.toml` / `setup.py` — dependencies, entry points

```bash
# Create/update index (indexes README.md + all Python)
python3 ~/.claude/scripts/build_code_index.py . --include-readme

# Query before exploring
python3 ~/.claude/scripts/query_code.py func "X"      # Find function
python3 ~/.claude/scripts/query_code.py class "Y"     # Find class
python3 ~/.claude/scripts/query_code.py context       # README + structure
```

**Required:** Query code_index first. Read README.md for project context. No blind exploration.

## Python Workflow

| Task           | Load                                                          |
| -------------- | ------------------------------------------------------------- |
| New code       | [[python/style]] → [[python/violations]] → [[python/bugs]]    |
| Tests          | [[python/testing]] + [[python/conftest]] + [[python/mocking]] |
| Property tests | [[python/property-testing]]                                   |
| Bug fix        | [[python/bugs]] → verify with test                            |
| Security       | [[python/security]]                                           |

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
