# Recipe Structure & Requirements

## Recipe Structure

### Required Sections

| Section        | Purpose                      | Notes                                            |
| -------------- | ---------------------------- | ------------------------------------------------ |
| `package`      | name + version               | Multi-output: name must differ from output names |
| `build`        | build number, scripts        | Always required, even for multi-output           |
| `requirements` | build/host/run deps          | Multi-output: per-output requirements            |
| `test`         | imports/commands/files       | Multi-output: per-output test sections           |
| `about`        | home, license, summary, URLs | SPDX license, license_family required            |

### Optional Sections

- `source`: url/git_url/path + sha256 checksum
- `extra`: maintainers, lint skips

### Build Section

`number: 0` required. pip flags: `--no-deps` (conda manages), `--no-build-isolation` (PEP 518 deps in host).

### noarch

`noarch: python` (pure Python) or `noarch: generic` (static). No compiled extensions, no platform selectors.

### Multi-Output Recipes

<!-- prettier-ignore-start -->
```yaml
package:
  name: mypackage-split # must differ from output names
  version: "1.0"

build:
  number: 0

outputs:
  - name: libmypackage
    script: install_lib.sh # unique script names
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
<!-- prettier-ignore-end -->

## Requirements Section

### Three Dependency Types

| Type    | When Used                      | Examples                           |
| ------- | ------------------------------ | ---------------------------------- |
| `build` | Build tools, cross-compilation | compilers, cmake, make, patch, git |
| `host`  | Link-time deps                 | python, numpy, libraries           |
| `run`   | Runtime deps                   | python, imported packages          |

### Compiler Syntax

<!-- prettier-ignore-start -->
```yaml
requirements:
  build:
    - {{ compiler('c') }}
    - {{ compiler('cxx') }}
    - {{ compiler('fortran') }} # if needed
    - {{ compiler('cuda') }} # GPU packages
    - {{ stdlib('c') }} # C standard library
```
<!-- prettier-ignore-end -->

### Host Pinnings

Exact versions preferred. Exception: cbc.yaml implicit pins. Build tools: `setuptools`/`wheel`/`pip` or modern.
