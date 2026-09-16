---
name: python/pixi-pyproject
description: Creating pyproject.toml with pixi package manager
invocation: auto
---

# Pixi pyproject.toml

## Minimal

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">= 3.12"

[tool.pixi.project]
channels = ["conda-forge"]
platforms = ["osx-arm64", "osx-64", "linux-64", "win-64"]
```

## Dependencies

```toml
[tool.pixi.dependencies]           # Conda-forge (prefer for compiled)
python = ">=3.12"
numpy = ">=1.26"

[tool.pixi.pypi-dependencies]      # PyPI fallback
my-project = { path = ".", editable = true }
```

Specifiers: `">=1.0"` `">=1.0,<2"` `"*"` `"==1.2.3"`

## Features/Environments

```toml
[tool.pixi.feature.dev.dependencies]
pytest = ">=8.0"
ruff = ">=0.4"

[tool.pixi.environments]
default = { solve-group = "default" }
dev = { features = ["dev"], solve-group = "default" }
```

## Tasks

```toml
[tool.pixi.tasks]
test = "pytest tests/"
check = { depends-on = ["lint", "test"] }
```

## Build System

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Commands

`pixi init` | `pixi add pkg` | `pixi add --pypi pkg` | `pixi add --feature dev pkg` | `pixi run task` | `pixi shell`
