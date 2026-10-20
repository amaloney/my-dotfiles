---
name: conda
description: Conda-first development - package mgmt, envs, lockfiles, full paths
invocation: auto
keywords: ["conda"]
---

# Conda Development

Handoff: `next: done`.

## Registry

| Skill                    | Purpose                   | Triggers                                   |
| ------------------------ | ------------------------- | ------------------------------------------ |
| [[conda-packaging]]      | Package building          | recipe, meta.yaml, pinnings, build         |
| [[conda-internal]]       | Anaconda-internal tooling | aggregate, PBP, AnacondaRecipes            |
| [[conda-anaconda-tools]] | Anaconda enterprise tools | auth, client, audit, menuinst, constructor |

## Package Priority

| Priority | Source                           | When                   |
| -------- | -------------------------------- | ---------------------- |
| 1        | `conda install` (defaults)       | Always try first       |
| 2        | `conda install -c conda-forge`   | Not in defaults        |
| 3        | `pip install` (inside conda env) | PyPI-only, pure Python |

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
  - pip
  - pip:
      - pypi-only-pkg
```

## Mixing Conda + Pip

Conda first → then pip → never `conda install` after pip. Document pip deps in `pip:` section.

## Policy

Conda first. Environments only. Lock for prod. Full paths. No venv. Commit environment.yml + lockfiles.

## Virtual Packages

`conda info` shows __glibc, __cuda, __osx, __archspec — auto-detected system constraints for solver.

## Troubleshooting

| Problem           | Fix                                                                      |
| ----------------- | ------------------------------------------------------------------------ |
| Command not found | Use full path: `$(which cmd)`                                            |
| Slow solver       | libmamba solver is default (conda 23.10+); try `mamba`                   |
| Dep conflicts     | Fresh env, install one-by-one                                            |
| Broken after pip  | Recreate: `conda env remove -n X && conda env create -f environment.yml` |

## Modern Tools

pixi (auto-lockfiles), mamba (faster), libmamba solver (default 23.10+).

## Conda in PowerShell

`. (Join-Path $env:CONDA_PREFIX "shell\condabin\conda-hook.ps1"); conda activate $env:CONDA_PREFIX`
