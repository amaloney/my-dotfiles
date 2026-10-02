---
name: python/modern-tooling
description: Modern Python tooling - uv, ruff, ty (replaces pip, black/flake8, mypy)
invocation: auto
---

# Modern Python Tooling

## Tool Mapping

pip/virtualenv/pip-tools → `uv`; pipx → `uv tool`; flake8/black/isort/pyupgrade → `ruff`; mypy/pyright → `ty`; pre-commit → `prek`.

## uv Commands

| Task                | Command                         | Replaces                          |
| ------------------- | ------------------------------- | --------------------------------- |
| Create project      | `uv init myproject`             | —                                 |
| Add dependency      | `uv add requests`               | `pip install requests`            |
| Add dev dependency  | `uv add --dev pytest`           | —                                 |
| Remove dependency   | `uv remove requests`            | `pip uninstall requests`          |
| Sync environment    | `uv sync`                       | `pip install -e .` (auto editable) |
| Run script          | `uv run python script.py`       | `python script.py`                |
| Export requirements | `uv export > requirements.txt`  | `pip freeze`                      |
| Install CLI tool    | `uv tool install ruff`          | `pipx install ruff`               |
| Run CLI tool once   | `uvx ruff check .`              | `pipx run ruff`                   |

## ruff Commands

```bash
ruff check .                    # lint
ruff check --fix .              # lint + auto-fix
ruff format .                   # format (replaces black)
ruff check --select I --fix .   # fix imports only (replaces isort)
```

### pyproject.toml Config

Canonical ruff select list (single statement): `select = ["E", "F", "I", "UP", "B", "SIM", "ANN", "ASYNC", "S"]`.

```toml
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"

[tool.ruff.lint]
# select list: see canonical statement above
fixable = ["E", "F", "I"]
unfixable = []

[tool.ruff.lint.isort]
known-first-party = ["<package_name>"]

[tool.ruff.lint.flake8-quotes]
docstring-quotes = "double"

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "S310"]  # assert + urlopen in tests
```

## ty Commands

```bash
ty check .                      # type check (add --watch for watch mode)
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
```

Commands: `uv init --script s.py`, `uv add --script s.py requests`, `uv run s.py`.

**Use PEP 723 for:** single-file scripts, quick automation, self-contained utilities.
**Use pyproject.toml for:** multi-file projects, reusable packages.

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
uv add --group dev pytest       # add to group; `uv sync --all-groups` installs all
```

## pyproject.toml Full Example

See [references/pyproject.md](references/pyproject.md).

## Decision Tree

```
What are you building?
├── Single-file script with deps? → PEP 723 inline metadata
├── Multi-file project (not distributed)? → uv init + minimal pyproject.toml
└── Reusable package/library? → uv init --package + full pyproject.toml
```

[[python/pixi-pyproject]] [[python/violations]] [[python/style]]
