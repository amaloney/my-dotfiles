# GPU & OpenMP Platforms

## GPU Packages

### CUDA

<!-- prettier-ignore-start -->
```yaml
requirements:
  build:
    - {{ compiler('c') }}
    - {{ compiler('cuda') }}
  host:
    - cuda-version # pins CUDA version
    # Add specific CUDA libs as needed:
    - libcublas-dev
    - cudnn
```
<!-- prettier-ignore-end -->

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
MACOSX_SDK_VERSION: # [osx and arm64]
  - "12.3" # [osx and arm64]
```

```bash
# build.sh
export USE_MPS=1
```

## OpenMP

### Default Runtimes

| Platform        | Non-MKL Build | MKL Build      |
| --------------- | ------------- | -------------- |
| Linux           | `libgomp`     | `intel-openmp` |
| macOS           | `llvm-openmp` | `intel-openmp` |
| Windows x86/x64 | `vcomp14`     | `intel-openmp` |

### Recipe Pattern

<!-- prettier-ignore-start -->
```yaml
requirements:
  build:
    - {{ compiler('c') }}
  host:
    - libgomp # [linux]
    - llvm-openmp # [osx]
    - vcomp14 # [win and x86]
```
<!-- prettier-ignore-end -->

**Critical**: Never mix OpenMP runtimes. `_openmp_mutex` metapackage enforces one family per environment.
