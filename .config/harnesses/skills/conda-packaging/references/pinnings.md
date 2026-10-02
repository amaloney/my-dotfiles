# Pinnings, run_exports & cbc.yaml

## Pinnings

### Explicit vs Implicit

```yaml
# Explicit pin
requirements:
  host:
    - libpng >=1.6

# Implicit pin (from conda_build_config.yaml)
requirements:
  host:
    - numpy {{ numpy }} # or just `- numpy` if key exists in cbc
```

### run_exports

When library X declares `run_exports`, adding X to `host:` auto-adds it to `run:` with proper pin.

```yaml
# In library's recipe
build:
  run_exports:
    - {{ pin_subpackage('mylib', max_pin='x.x') }}  # weak (default)
    # OR
    weak:
      - {{ pin_subpackage('mylib', max_pin='x.x') }}
    strong:  # applies even from build: section
      - libgcc
```

**Weak vs Strong**:

- `weak`: applies when in `host:`, adds to `run:`
- `strong`: applies from `build:` too (runtimes like libgcc)

### run_exports with Constraints

```yaml
build:
  run_exports:
    weak_constrains:
      - optional-plugin >=2.0 # adds to run_constrained
    strong_constrains:
      - system-feature >=1.0
```

### Pin Guidelines

| Scenario                 | Recommendation                                       |
| ------------------------ | ---------------------------------------------------- |
| C/C++ libs               | Pin to major or `x.x` matching run_exports           |
| NumPy (C API)            | `numpy {{ numpy }}` in host, `pin_compatible` in run |
| Pure Python deps         | Follow upstream requirements                         |
| Applications (CLI tools) | Stricter pins OK, but avoid ecosystem conflicts      |

### run_constrained

Express conflicts or optional deps without forcing install:

```yaml
run_constrained:
  - conflicting-pkg <0 # never install together
  - optional-feature >=2.0 # if installed, must be >=2.0
```

### Pinning Expressions

```yaml
pin_run_as_build:
  boost:
    max_pin: x.x # >=1.65.1,<1.66 if built with 1.65.1
    min_pin: x.x.x # lower bound at exact version
```

| Expression | Result for 1.65.1 |
| ---------- | ----------------- |
| `x`        | >=1,<2            |
| `x.x`      | >=1.65,<1.66      |
| `x.x.x`    | >=1.65.1,<1.65.2  |

## conda_build_config.yaml (cbc.yaml)

### Scope

- **Global**: aggregate root, applies to all recipes when building from there
- **Local**: recipe folder, overrides global
- **meta.yaml**: inline values override both

### Search Order

1. `conda_build_config.yaml` in HOME folder (or .condarc `conda_build/config_file`)
2. `conda_build_config.yaml` in current working directory
3. `conda_build_config.yaml` in recipe folder (same as meta.yaml)

### Key Features

```yaml
# Multiple variants → build matrix
python:
  - "3.10"
  - "3.11"
  - "3.12"

# Platform selectors
perl:
  - 5.26 # [win]
  - 5.34 # [not win]

# Paired variants (no matrix explosion)
zip_keys:
  - [python, numpy]

# Extend instead of override
extend_keys:
  - ignore_build_only_deps

# Runtime pin from build-time version
pin_run_as_build:
  boost:
    max_pin: x.x

# Core dependency tree (Linux only)
cdt_name:
  - amzn2 # [linux and aarch64]
```

### Environment Variables

```yaml
MACOSX_SDK_VERSION: # [osx]
  - "10.14" # [osx]
CONDA_BUILD_SYSROOT: # [osx]
  - /opt/MacOSX10.14.sdk # [osx]
```

## Platform Selectors

| Selector  | linux-64 | linux-aarch64 | osx-arm64 | win-64 | win-arm64 |
| --------- | -------- | ------------- | --------- | ------ | --------- |
| `linux`   | ✓        | ✓             |           |        |           |
| `linux64` | ✓        |               |           |        |           |
| `osx`     |          |               | ✓         |        |           |
| `unix`    | ✓        | ✓             | ✓         |        |           |
| `win`     |          |               |           | ✓      | ✓         |
| `win64`   |          |               |           | ✓      |           |
| `x86_64`  | ✓        |               |           | ✓      |           |
| `aarch64` |          | ✓             |           |        |           |
| `arm64`   |          |               | ✓         |        | ✓         |
