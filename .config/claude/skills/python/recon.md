---
name: python/recon
description: Profile Python project - outputs .claude/code_index/profile.json
invocation: manual
---

# Python Project Recon

Run FIRST before other Python skills. Outputs `.claude/code_index/profile.json`.

## When to Run

- Session start in Python repo
- After major refactor
- When profile.json missing or stale (>7 days)

## Protocol

### 1. Detect Project Type

```bash
# Check markers
test -f pyproject.toml && echo "pyproject"
test -f setup.py && echo "setup.py"
test -f pixi.toml && echo "pixi"
test -d src && echo "src-layout"
fd -e py -d 1 . | head -1 && echo "flat-layout"
```

| Markers | Type |
|---------|------|
| `cli.py`, `__main__.py`, Click/Typer dep | cli |
| Only `__init__.py`, no entry points | library |
| Flask/Django/FastAPI dep | webapp |
| pandas/numpy heavy, notebooks | datascience |
| Multiple `pyproject.toml` | monorepo |

### 2. Map Structure

```bash
# Source directories
fd -t d -d 2 "src|lib" .
fd "__init__.py" -x dirname {} | sort -u | head -10

# Test directories  
fd -t d "tests|test" -d 2 .

# Config files
fd -g "config.py" .
fd -g "settings.py" .
```

### 3. Find Constants

```bash
# ALL_CAPS assignments outside functions/classes
rg -n "^[A-Z][A-Z_0-9]+ ?=" --type py | head -30

# Env var access patterns
rg -n "os\.environ|os\.getenv|environ\.get" --type py | head -20
```

### 4. Detect Tooling

```bash
# From pyproject.toml
rg "^\[tool\." pyproject.toml | sed 's/\[tool\.//' | tr -d ']'

# Test framework
test -f pytest.ini && echo "pytest"
rg "pytest" pyproject.toml && echo "pytest"
rg "unittest" -l --type py tests/ && echo "unittest"
```

### 5. Write Profile

```bash
mkdir -p .claude/code_index
```

Output to `.claude/code_index/profile.json`:

```json
{
  "version": "1.0",
  "generated": "<ISO timestamp>",
  "project": {
    "name": "<from pyproject.toml or dir name>",
    "type": "<cli|library|webapp|datascience|monorepo>",
    "python_version": "<from pyproject.toml>",
    "src_layout": "<flat|src|packages>"
  },
  "structure": {
    "src_dirs": ["<paths>"],
    "test_dirs": ["<paths>"],
    "config_files": ["<paths>"],
    "entry_points": ["<paths>"]
  },
  "patterns": {
    "config_py_path": "<path or null>",
    "constants_locations": [{"file": "<path>", "line": "<n>", "name": "<NAME>"}],
    "scattered_constants": [{"file": "<path>", "line": "<n>", "name": "<NAME>"}]
  },
  "testing": {
    "framework": "<pytest|unittest|none>",
    "fixtures_in": ["<paths>"]
  },
  "linting": {
    "tool": "<ruff|flake8|none>",
    "type_checker": "<ty|mypy|pyright|none>"
  }
}
```

### 6. Validation

After writing, verify:

```bash
cat .claude/code_index/profile.json | jq '.'
```

## Usage by Other Skills

Skills read profile.json instead of scanning:

```python
# In skill prompt
"Read .claude/code_index/profile.json first.
 Constants should be in: {profile.patterns.config_py_path}
 Currently scattered in: {profile.patterns.scattered_constants}"
```

## Staleness Check

```bash
# Profile older than 7 days?
find .claude/code_index/profile.json -mtime +7 2>/dev/null && echo "stale"
```

[[python]] [[python/structure]] [[python/org]]
