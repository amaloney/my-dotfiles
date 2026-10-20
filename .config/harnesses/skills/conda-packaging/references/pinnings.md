# Pinnings, run_exports & cbc.yaml

## Pinnings

**Explicit**: `- libpng >=1.6` in host. **Implicit**: `- numpy {{ numpy }}` from conda_build_config.yaml.

### run_exports

Library declares `run_exports` → host dep auto-adds to run. `weak`: from host only. `strong`: from build too (runtimes).

### run_exports Constraints

`weak_constrains` / `strong_constrains` add to run_constrained.

### Pin Guidelines

| Scenario                 | Recommendation                                       |
| ------------------------ | ---------------------------------------------------- |
| C/C++ libs               | Pin to major or `x.x` matching run_exports           |
| NumPy (C API)            | `numpy {{ numpy }}` in host, `pin_compatible` in run |
| Pure Python deps         | Follow upstream requirements                         |
| Applications (CLI tools) | Stricter pins OK, but avoid ecosystem conflicts      |

### run_constrained

Conflicts/optional deps without forcing install: `conflicting-pkg <0`, `optional-feature >=2.0`.

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

Global (aggregate) → Local (recipe) → meta.yaml inline. Search: HOME → cwd → recipe folder.

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
