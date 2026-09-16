---
name: conda
description: Conda-first development - package mgmt, envs, lockfiles, full paths
invocation: auto
---

# Conda Development

## Package Priority

| Priority | Source                           | When                   |
| -------- | -------------------------------- | ---------------------- |
| 1        | `conda install` (defaults)       | Always try first       |
| 2        | `conda install -c conda-forge`   | Not in defaults        |
| 3        | `pip install` (inside conda env) | PyPI-only, pure Python |

**Performance packages ALWAYS conda**: numpy, scipy, pandas, sklearn, pytorch, tensorflow, matplotlib, h5py, pyarrow

## Commands

```bash
# Create env
conda create -n proj python=3.11
conda activate proj

# Install
conda install numpy pandas    # defaults first
conda install -c conda-forge pkg    # if needed

# Export
conda env export --from-history > environment.yml

# Lockfile (reproducibility)
conda-lock -f environment.yml -p linux-64 -p osx-64
conda-lock install --name proj conda-lock.yml

# Update
conda env update -f environment.yml --prune
```

## Full Paths Required

**NEVER `python script.py`** — use full path:

```bash
/opt/miniconda3/envs/proj/bin/python script.py
$(which python) -m pytest tests/
```

| ❌ Wrong        | ✅ Correct                       |
| --------------- | -------------------------------- |
| `python app.py` | `/path/to/env/bin/python app.py` |
| `pytest`        | `$(which pytest)`                |
| `black .`       | `/path/to/env/bin/black .`       |

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

1. Install ALL conda packages first
2. Then pip packages
3. Document pip deps in `pip:` section
4. **Never** re-run `conda install` after pip

## Decision Tree

```
Package needed?
├─ Performance/scientific (numpy, torch)? → ALWAYS conda
├─ Has compiled code/native deps?
│  ├─ In defaults? → conda install
│  ├─ In conda-forge? → conda install -c conda-forge
│  └─ Neither? → pip install (in conda env)
└─ Pure Python?
   ├─ In conda? → conda install
   └─ PyPI only? → pip install (in conda env)
```

## Policy

1. **Conda first** — defaults → conda-forge → pip
2. **Environments only** — never global
3. **Lock it** — conda-lock for prod
4. **Full paths always** — explicit > implicit
5. **No venv** — conda envs only
6. **Commit** — environment.yml + lockfiles to git

## Virtual Packages

```bash
conda info    # Shows __glibc, __cuda, __osx, __archspec
```

Auto-detected system constraints for solver (GPU drivers, glibc version, CPU arch).

## Troubleshooting

| Problem           | Fix                                                                      |
| ----------------- | ------------------------------------------------------------------------ |
| Command not found | Use full path: `$(which cmd)`                                            |
| Slow solver       | `conda config --set solver libmamba`                                     |
| Dep conflicts     | Fresh env, install one-by-one                                            |
| Broken after pip  | Recreate: `conda env remove -n X && conda env create -f environment.yml` |

## Modern Tools

- **pixi**: Auto-lockfiles, faster. `pixi add pkg`
- **mamba**: Drop-in faster conda. `mamba install pkg`
- **libmamba solver**: Default in conda 23.10+
