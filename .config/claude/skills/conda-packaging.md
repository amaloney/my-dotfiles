# Conda Package Building

Dense reference for building conda packages with conda-build. Focus: recipe authoring, dependencies, pinnings, troubleshooting.

## Recipe Structure

### Required Sections

| Section        | Purpose                              | Notes                                              |
| -------------- | ------------------------------------ | -------------------------------------------------- |
| `package`      | name + version                       | Multi-output: name must differ from output names   |
| `build`        | build number, scripts                | Always required, even for multi-output             |
| `requirements` | build/host/run deps                  | Multi-output: per-output requirements              |
| `test`         | imports/commands/files               | Multi-output: per-output test sections             |
| `about`        | home, license, summary, URLs         | SPDX license, license_family required              |

### Optional Sections

- `source`: url/git_url/path + sha256 checksum
- `extra`: maintainers, lint skips

### Build Section Rules

```yaml
build:
  number: 0  # required, increment for rebuilds of same version
  script: pip install . --no-deps --no-build-isolation -vv  # if no build.sh/bld.bat
  # noarch: python  # only pure-python, no compiled extensions, no platform selectors
```

**pip install flags**:
- `--no-deps`: conda manages deps, not pip
- `--no-build-isolation`: PEP 518 deps already in host

### noarch Packages

```yaml
build:
  noarch: python  # pure Python, any Python version
  # OR
  noarch: generic  # static assets, source archives
```

**noarch: python requirements**:
- No compiled extensions (C/C++/Rust)
- No platform selectors in recipe
- Works across all Python versions

### Multi-Output Recipes

```yaml
package:
  name: mypackage-split  # must differ from output names
  version: "1.0"

build:
  number: 0

outputs:
  - name: libmypackage
    script: install_lib.sh  # unique script names
    requirements:
      run:
        - some-dep
    test:
      commands:
        - test -f $PREFIX/lib/libmypackage.so

  - name: mypackage
    script: install_pkg.sh
    requirements:
      run:
        - {{ pin_subpackage('libmypackage', exact=True) }}
        - python
    test:
      imports:
        - mypackage
```

## Requirements Section

### Three Dependency Types

| Type    | When Used                      | Examples                                   |
| ------- | ------------------------------ | ------------------------------------------ |
| `build` | Build tools, cross-compilation | compilers, cmake, make, patch, git         |
| `host`  | Link-time deps                 | python, numpy, libraries                   |
| `run`   | Runtime deps                   | python, imported packages                  |

### Compiler Syntax

```yaml
requirements:
  build:
    - {{ compiler('c') }}
    - {{ compiler('cxx') }}
    - {{ compiler('fortran') }}  # if needed
    - {{ compiler('cuda') }}     # GPU packages
    - {{ stdlib('c') }}          # C standard library
```

### Host Section Pinnings

- Exact versions preferred, no comparison operators
- Exception: packages in `conda_build_config.yaml` (implicit pinning)
- Python build tools required for pip install: `setuptools`, `wheel`, `pip`, or modern (`hatchling`, `flit-core`, `meson-python`, etc.)

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
    - numpy {{ numpy }}  # or just `- numpy` if key exists in cbc
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
      - optional-plugin >=2.0  # adds to run_constrained
    strong_constrains:
      - system-feature >=1.0
```

### Pin Guidelines

| Scenario                 | Recommendation                                            |
| ------------------------ | --------------------------------------------------------- |
| C/C++ libs               | Pin to major or `x.x` matching run_exports                |
| NumPy (C API)            | `numpy {{ numpy }}` in host, `pin_compatible` in run      |
| Pure Python deps         | Follow upstream requirements                              |
| Applications (CLI tools) | Stricter pins OK, but avoid ecosystem conflicts           |

### run_constrained

Express conflicts or optional deps without forcing install:

```yaml
run_constrained:
  - conflicting-pkg <0  # never install together
  - optional-feature >=2.0  # if installed, must be >=2.0
```

### Pinning Expressions

```yaml
pin_run_as_build:
  boost:
    max_pin: x.x  # >=1.65.1,<1.66 if built with 1.65.1
    min_pin: x.x.x  # lower bound at exact version
```

| Expression | Result for 1.65.1    |
| ---------- | -------------------- |
| `x`        | >=1,<2               |
| `x.x`      | >=1.65,<1.66         |
| `x.x.x`    | >=1.65.1,<1.65.2     |

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
  - 5.26  # [win]
  - 5.34  # [not win]

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
  - amzn2  # [linux and aarch64]
```

### Environment Variables

```yaml
MACOSX_SDK_VERSION:           # [osx]
  - "10.14"                   # [osx]
CONDA_BUILD_SYSROOT:          # [osx]
  - /opt/MacOSX10.14.sdk      # [osx]
```

## Platform Selectors

| Selector   | linux-64 | linux-aarch64 | osx-arm64 | win-64 | win-arm64 |
| ---------- | -------- | ------------- | --------- | ------ | --------- |
| `linux`    | ✓        | ✓             |           |        |           |
| `linux64`  | ✓        |               |           |        |           |
| `osx`      |          |               | ✓         |        |           |
| `unix`     | ✓        | ✓             | ✓         |        |           |
| `win`      |          |               |           | ✓      | ✓         |
| `win64`    |          |               |           | ✓      |           |
| `x86_64`   | ✓        |               |           | ✓      |           |
| `aarch64`  |          | ✓             |           |        |           |
| `arm64`    |          |               | ✓         |        | ✓         |

## Testing

### Minimum Test Section

```yaml
test:
  imports:
    - mypackage
  commands:
    - pip check  # requires pip in test/requires
  requires:
    - pip
```

**Rules**:
- Don't add `commands:` if `run_test.sh`/`run_test.bat` exist (conda-build skips them)
- Multi-output: unique test script names per output
- Add `files:` if test scripts in recipe dir

### Local Testing

```bash
# Build package
conda build recipe/ --error-overlinking --error-overdepending

# Inspect built package
conda search <package> -c local -i

# Test in fresh env
conda create -n test-env -c local <package>
conda activate test-env
# run tests
```

## Patches

### Creating Patches

```bash
git clone <upstream>
git checkout tags/<version>
# make changes
git diff > 0001-descriptive-name.patch
```

### Getting Patch from PR

```bash
curl -L https://github.com/org/repo/pull/123.patch -o 0001-fix-thing.patch
# For merged PR, use merge commit for traceability
```

### meta.yaml

```yaml
source:
  url: https://...
  sha256: ...
  patches:
    # See https://github.com/org/repo/pull/123
    # Can be removed in version X.Y+
    - patches/0001-fix-thing.patch

requirements:
  build:
    - patch       # [unix]
    - m2-patch    # [win]
```

**Best practices**:
- Keep original author/commit info
- Link to upstream PR/issue
- Note when patch can be dropped

## GPU Packages

### CUDA

```yaml
requirements:
  build:
    - {{ compiler('c') }}
    - {{ compiler('cuda') }}
  host:
    - cuda-version  # pins CUDA version
    # Add specific CUDA libs as needed:
    - libcublas-dev
    - cudnn
```

Build script enables CUDA:
```bash
# Varies by build system
cmake -DUSE_CUDA=ON ...
# OR
export USE_CUDA=1
```

**Note**: `cuda-version` package declares `__cuda` in `run_constrained`, auto-enforcing compatible GPU.

### Metal/MPS (macOS)

```yaml
# conda_build_config.yaml
MACOSX_SDK_VERSION:    # [osx and arm64]
  - "12.3"             # [osx and arm64]
```

```bash
# build.sh
export USE_MPS=1
```

## OpenMP

### Default Runtimes

| Platform         | Non-MKL Build | MKL Build       |
| ---------------- | ------------- | --------------- |
| Linux            | `libgomp`     | `intel-openmp`  |
| macOS            | `llvm-openmp` | `intel-openmp`  |
| Windows x86/x64  | `vcomp14`     | `intel-openmp`  |

### Recipe Pattern

```yaml
requirements:
  build:
    - {{ compiler('c') }}
  host:
    - libgomp       # [linux]
    - llvm-openmp   # [osx]
    - vcomp14       # [win and x86]
```

**Critical**: Never mix OpenMP runtimes. `_openmp_mutex` metapackage enforces one family per environment.

## Common Errors

### Hunk FAILED

Patch outdated for current source version. Re-generate patch against new version.

### Checksum Mismatch

Wrong sha256 for version. Verify hash matches download.

### UnsatisfiableError

Conflicting version constraints. Debug:

```bash
conda create -n test --dry-run <package>=<version>
```

### DependencyNeedsBuildingError

Dependency not built for platform. Build it first or skip platform with `skip: True  # [platform]`.

### Overlinking

Binary links to library not in declared deps but present transitively.

**Fix**: Add to `run:` or upstream's `run_exports:`. Don't suppress this.

### Overdepending

Recipe declares dep not actually linked. False positive if:
- Library loaded at runtime (dlopen)
- Static linking used

**Suppress**: Add to `build/ignore_run_exports` with justification.

### Missing DSO / Whitelist Error

Binary needs library not in deps or environment. Either:
1. Add missing dep to `run:`
2. If system lib (libc, libpthread): add to `build/missing_dso_whitelist`

### ModuleNotFoundError

- Missing from correct section (host vs run vs test/requires)
- Misspelled
- Wrong version removed the module

### pip check Errors

Version mismatch vs upstream requirements. Fix pin or disable `pip check` with justification.

### CMake RPATH Issue (macOS)

Overlinking error pointing to `$SRC_DIR/build/...`:

**Fix**: Set `CMAKE_BUILD_WITH_INSTALL_RPATH=ON` to avoid build-time RPATH.

## Linter Checks

Common lint rules to satisfy:

| Rule                              | Fix                                           |
| --------------------------------- | --------------------------------------------- |
| `missing_build_number`            | Add `build/number`                            |
| `compilers_must_be_in_build`      | Move `{{ compiler() }}` to `build:` section   |
| `build_tools_must_be_in_build`    | Move cmake/make/git to `build:` section       |
| `host_section_needs_exact_pinnings` | Use exact versions, not ranges             |
| `missing_hash`                    | Add `sha256:` to source                       |
| `invalid_spdx_expression`         | Use valid SPDX license identifier             |
| `missing_pip_check`               | Add `pip check` to test commands              |
| `pip_install_args`                | Use `--no-deps --no-build-isolation`          |
| `deprecated_python_install_command` | Replace `setup.py install` with pip         |

## Tools

### conda-build CLI

```bash
conda build recipe/ [options]
  --error-overlinking      # fail on overlinking
  --error-overdepending    # fail on overdepending
  -c <channel>             # add channel
  --croot <dir>            # build root
  --output-folder <dir>    # where to put packages
```

### conda-recipe-manager (crm)

```bash
# Bump version
crm bump-recipe -t <new-version> recipe/meta.yaml

# Increment build number only
crm bump-recipe --build-num recipe/meta.yaml

# Convert V0 (meta.yaml) to V1 (recipe.yaml)
crm convert recipe/meta.yaml
```

### Verification

```bash
# View package metadata
conda search <package> -c local -i

# Check linkages (Linux)
conda inspect linkages <package>

# Check imported packages (Python)
conda inspect objects <package>
```

---
