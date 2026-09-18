---
name: python/modern-tooling
description: Modern Python tooling - uv, ruff, ty (replaces pip, black/flake8, mypy)
invocation: auto
---

# Modern Python Tooling

## Tool Mapping

| Legacy                          | Modern    | Purpose                |
| ------------------------------- | --------- | ---------------------- |
| pip, virtualenv, pip-tools      | `uv`      | Package/env management |
| pipx                            | `uv tool` | CLI tool installation  |
| flake8, black, isort, pyupgrade | `ruff`    | Lint + format          |
| mypy, pyright                   | `ty`      | Type checking          |
| pre-commit                      | `prek`    | Git hooks              |

## uv Commands

| Task                | Command                         |
| ------------------- | ------------------------------- |
| Create project      | `uv init myproject`             |
| Add dependency      | `uv add requests`               |
| Add dev dependency  | `uv add --dev pytest`           |
| Remove dependency   | `uv remove requests`            |
| Sync environment    | `uv sync`                       |
| Run script          | `uv run python script.py`       |
| Run with temp dep   | `uv run --with httpx script.py` |
| Export requirements | `uv export > requirements.txt`  |
| Install CLI tool    | `uv tool install ruff`          |
| Run CLI tool once   | `uvx ruff check .`              |

### Equivalents

| pip/pipx            | uv                        |
| ------------------- | ------------------------- |
| `pip install pkg`   | `uv add pkg`              |
| `pip install -e .`  | `uv sync` (auto editable) |
| `pip uninstall pkg` | `uv remove pkg`           |
| `pip freeze`        | `uv export`               |
| `pipx install pkg`  | `uv tool install pkg`     |
| `pipx run pkg`      | `uvx pkg`                 |
| `python script.py`  | `uv run python script.py` |
| `python -m pytest`  | `uv run pytest`           |

## ruff Commands

```bash
ruff check .                    # lint
ruff check --fix .              # lint + auto-fix
ruff format .                   # format (replaces black)
ruff check --select I --fix .   # fix imports only (replaces isort)
```

### pyproject.toml Config

```toml
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = [
    "E", "F",     # pycodestyle, pyflakes
    "I",          # isort
    "UP",         # pyupgrade
    "B",          # bugbear
    "SIM",        # simplify
    "ANN",        # annotations
    "ASYNC",      # async
    "S",          # bandit (security)
]
ignore = ["ANN101", "ANN102"]  # self/cls annotation

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]  # allow assert in tests
```

## ty Commands

```bash
ty check .                      # type check
ty check --watch .              # watch mode
ty check src/module.py          # single file
```

### pyproject.toml Config

```toml
[tool.ty]
python-version = "3.12"
strict = true

[tool.ty.overrides]
"tests/**" = { strict = false }
```

## Security Tools

| Tool             | Purpose                    | Command                 |
| ---------------- | -------------------------- | ----------------------- |
| `pip-audit`      | Dependency vulnerabilities | `uv run pip-audit`      |
| `detect-secrets` | Secrets in code            | `detect-secrets scan`   |
| `bandit`         | Security lints             | `ruff check --select S` |
| `zizmor`         | GitHub Actions audit       | `zizmor .github/`       |

## PEP 723: Inline Script Metadata

For single-file scripts with dependencies — no pyproject.toml needed:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
#     "rich",
# ]
# ///

import requests
from rich import print

print(requests.get("https://httpbin.org/ip").json())
```

| Task | Command |
|------|---------|
| Create script | `uv init --script myscript.py` |
| Add dep to script | `uv add --script myscript.py requests` |
| Run script | `uv run myscript.py` |

**Use PEP 723 for:** Single-file scripts, quick automation, self-contained utilities
**Use pyproject.toml for:** Multi-file projects, reusable packages

## Dependency Groups (PEP 735)

Prefer `[dependency-groups]` over `[project.optional-dependencies]` for dev tools:

```toml
[dependency-groups]
dev = [{include-group = "lint"}, {include-group = "test"}]
lint = ["ruff", "ty"]
test = ["pytest", "pytest-cov", "hypothesis"]
docs = ["sphinx", "myst-parser"]
```

```bash
uv add --group dev pytest       # Add to group
uv sync --group dev             # Install group
uv sync --all-groups            # Install all
```

## pyproject.toml Full Example

```toml
[project]
name = "myproject"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["requests>=2.31"]

[dependency-groups]
dev = [{include-group = "lint"}, {include-group = "test"}]
lint = ["ruff", "ty"]
test = ["pytest", "pytest-cov"]

[tool.ruff]
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.ty.environment]
python-version = "3.12"
```

## Decision Tree

```
What are you building?
├── Single-file script with deps? → PEP 723 inline metadata
├── Multi-file project (not distributed)? → uv init + minimal pyproject.toml
└── Reusable package/library? → uv init --package + full pyproject.toml
```

[[python/pixi-pyproject]] [[python/violations]] [[python/style]]
