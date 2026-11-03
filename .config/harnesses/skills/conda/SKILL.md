---
name: conda
description: Conda-only development - package management, environments, lockfiles, full paths
invocation: auto
keywords: ["conda"]
---

# Conda Development

Handoff: `next: done`.

## Registry

| Skill                    | Purpose                              | Triggers                                            |
| ------------------------ | ------------------------------------ | --------------------------------------------------- |
| [[conda-packaging]]      | Package building                     | recipe, meta.yaml, pinnings, build                  |
| [[conda-anaconda-tools]] | Anaconda enterprise tools + internal | auth, client, audit, menuinst, constructor, PBP     |

## Conda Environment Policy

Use Conda (`conda` / `conda run`) for Python environments, dependency management, and Python task execution. Do not use
`pip`, `pixi`, `uv`, or another Python environment/dependency manager. If a package is unavailable from configured Conda
channels, stop and report instead of falling back, even if project files or skills recommend another manager.

## Package Priority

1. Install from Conda defaults first: `conda install pkg`.
2. If unavailable, try Conda Forge: `conda install -c conda-forge pkg`.
3. If still unavailable, stop and report; do not use `pip` or another package manager.

**Performance packages ALWAYS conda**: numpy, scipy, pandas, sklearn, pytorch, tensorflow, matplotlib, h5py, pyarrow

## Commands

| Task    | Command                                                   |
| ------- | --------------------------------------------------------- |
| Create  | `conda create -n proj python=3.11 && conda activate proj` |
| Install | `conda install pkg` (defaults) or `-c conda-forge`        |
| Export  | `conda env export --from-history > environment.yml`       |
| Lock    | `conda-lock -f environment.yml -p linux-64 -p osx-64`     |
| Update  | `conda env update -f environment.yml --prune`             |

## Full Paths Required

**NEVER bare commands** — use `$(which python)` or full path `/path/to/env/bin/python`.

## environment.yml

```yaml
name: proj
channels:
  - defaults
  - conda-forge
dependencies:
  - python=3.11
  - numpy=1.26.*
  - pandas>=2.0
```

## Policy

Conda only. Environments only. Lock for prod. Full paths. No venv. Commit environment.yml + lockfiles.

## Virtual Packages

`conda info` shows __glibc, __cuda, __osx, __archspec — auto-detected system constraints for solver.

## Troubleshooting

| Problem           | Fix                                                        |
| ----------------- | ---------------------------------------------------------- |
| Command not found | Use full path: `$(which cmd)`                              |
| Slow solver       | libmamba solver is default (conda 23.10+); try `mamba`     |
| Dep conflicts     | Fresh env, install one-by-one                              |
| Package missing   | Stop and report; do not use pip or another package manager |

## Modern Tools

mamba (faster solver), libmamba solver (default 23.10+).

## Conda in PowerShell

`. (Join-Path $env:CONDA_PREFIX "shell\condabin\conda-hook.ps1"); conda activate $env:CONDA_PREFIX`
