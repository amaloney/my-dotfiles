---
name: python/modern-tooling
description: Conda-managed Ruff and pyrefly Python tooling
invocation: auto
---

# Python Tooling

Handoff: `next: python/structure`.

**Deprecated tools:** This skill documents Ruff and pyrefly only; never use uv or pip directly. For PyPI-only packages
unavailable from Conda channels, use `conda pypi install <pkg>`.

## Tool Mapping

flake8/black/isort/pyupgrade → `ruff`; mypy/pyright → `pyrefly`; pre-commit → `prek`.

Install and run these tools through the active Conda environment.

## ruff Commands

```bash
conda run -n proj ruff check .                    # lint
conda run -n proj ruff check --fix .              # lint + auto-fix
conda run -n proj ruff format .                   # format (replaces black)
conda run -n proj ruff check --select I --fix .   # fix imports only (replaces isort)
```

### pyproject.toml Config

Dependencies: ranged pins (`>=2.32,<3`), never `"*"`. Ruff select:
`["E", "F", "I", "UP", "B", "SIM", "ANN", "ASYNC", "S"]`.

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

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "S310"]  # assert + urlopen in tests
```

## pyrefly Commands

```bash
conda run -n proj pyrefly check .                 # type check
```

### pyproject.toml Config

```toml
[tool.pyrefly]
python-version = "3.12"

[tool.pyrefly.overrides]
"tests/**" = { ignore_errors = ["*"] }
```

## Security Tools

| Tool             | Purpose                    | Command                                   |
| ---------------- | -------------------------- | ----------------------------------------- |
| `pip-audit`      | Dependency vulnerabilities | `conda run -n proj pip-audit`             |
| `detect-secrets` | Secrets in code            | `conda run -n proj detect-secrets scan`   |
| `bandit`         | Security lints             | `conda run -n proj ruff check --select S` |
| `zizmor`         | GitHub Actions audit       | `zizmor .github/`                         |

## Decision Tree

Single-file → run with `conda run -n <env> python script.py`. Multi-file → use the repository's Conda environment.
Package → use its Conda recipe.

[[python/structure]]
