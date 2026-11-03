---
name: python/pixi-migration-reference
description: Reference for migrating Pixi-based Python projects to Conda
invocation: auto
keywords: ["pixi", "pyproject.toml", "pixi.toml"]
---

# Pixi Project Migration Reference

Handoff: `next: python/structure`.

This file is a legacy migration reference; do not apply to new work.

## Existing Project Structure

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">= 3.12"

[tool.pixi.workspace]               # not [tool.pixi.project]: deprecated name
channels = ["conda-forge"]
platforms = ["osx-arm64", "osx-64", "linux-64", "win-64"]
```

## Dependencies

```toml
[tool.pixi.dependencies]           # Existing legacy declarations; translate to Conda environment files
python = ">=3.12"
numpy = ">=1.26"

[tool.pixi.pypi-dependencies]       # Existing legacy declarations; do not install from PyPI
my-project = { path = ".", editable = true }
```

Specifiers: `">=1.0"` `">=1.0,<2"` `"*"` `"==1.2.3"`

## Features/Environments

```toml
[tool.pixi.feature.dev.dependencies] # Existing declarations; translate to Conda environment files
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

## Migration

Inspect `pyproject.toml` for existing `[tool.pixi.*]` sections and translate dependencies, environments, and tasks into
Conda equivalents. Do not invoke Pixi commands or retain Pixi as the environment manager.

[[python/modern-tooling]] [[python/structure]]
