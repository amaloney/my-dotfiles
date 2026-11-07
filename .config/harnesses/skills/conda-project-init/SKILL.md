---
name: conda-project-init
description: Scaffold a conda project in-place with src-layout, direnv, and pyproject.toml
invocation: manual
keywords: ["start conda project", "new conda project", "init conda", "create conda project", "scaffold"]
allowed-tools:
  - Bash
  - Read
  - Write
---

# Conda Project Init

Handoff: `next: done`.

Scaffold a conda project **in the current directory** with src-layout, direnv auto-activation, and modern Python tooling.

## When

User asks to:
- "create a new conda project" (in current directory)
- "init conda project"
- "scaffold conda project"

## Quick Path

```bash
# In the project directory (e.g., ~/projects/my-project)
~/.config/harnesses/skills/conda-project-init/conda-project-init.sh [name] [--kilo-isolated] [--full-xdg]
```

**Arguments:**
- `[name]` — Package name (optional, defaults to directory name with hyphens → underscores)

**Flags:**
- `--kilo-isolated` — Isolate kilo config to project
- `--full-xdg` — Full XDG isolation (all apps)

**Example:** In directory `my-project/`, running with no args creates package `my_project`.

## Result (in current directory)

```
./                          # current directory (e.g., my-project/)
├── .envrc                  # direnv config (auto-activates .conda/dev)
├── .condarc                # project-local conda config
├── .gitignore              # standard ignores
├── Makefile                # make env, make lock, make clean
├── environment.yaml        # conda environment spec (edit this)
├── pyproject.toml          # project metadata, ruff, pytest config (edit this)
├── README.md               # project readme
├── src/
│   └── my_project/         # package name (hyphens → underscores)
│       └── __init__.py     # package with __version__
└── tests/
    ├── __init__.py
    └── test_version.py     # starter test
```

## After Scaffold (tell user)

1. `direnv allow` — auto-activates `.conda/dev` on cd
2. Edit `environment.yaml` — uncomment/add dependencies
3. Edit `pyproject.toml` — fill in TODO placeholders (description, authors, license)
4. Run `make lock && make env` to rebuild with new dependencies

## Templates

Templates live at `~/.config/harnesses/conda/` (part of the harnesses symlink):

| File                 | Purpose                                    |
| -------------------- | ------------------------------------------ |
| `.envrc`             | direnv config with XDG isolation options   |
| `.condarc`           | project-local conda channels and settings  |
| `Makefile`           | env, lock, clean targets                   |
| `environment.yaml`   | conda deps with common packages commented  |
| `pyproject.toml`     | full config: ruff, pytest, hatch           |
| `.gitignore.template`| comprehensive Python/conda ignores         |

[[conda]]
