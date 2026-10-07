---
name: conda-packaging
description: Conda package building - recipes, dependencies, pinnings, troubleshooting
invocation: auto
keywords: ["conda package", "conda recipe", "meta.yaml", "conda-build"]
---

# Conda Package Building

Handoff: `next: done`.

Dense reference for building conda packages with conda-build. Focus: recipe authoring, dependencies, pinnings,
troubleshooting.

## Recipe Skeleton

```yaml
package:
  name: mypackage
  version: "1.0"

source:
  url: https://...
  sha256: ...

build:
  number: 0
  script: pip install . --no-deps --no-build-isolation -vv

requirements:
  build:
    - {{ compiler('c') }} # if compiled
  host:
    - python
  run:
    - python

test:
  imports:
    - mypackage
  requires:
    - pip
  commands:
    - pip check

about:
  home: https://...
  license: MIT
  license_family: MIT
  summary: ...
```

**pip install flags** (mandatory): `--no-deps` (conda manages deps), `--no-build-isolation` (PEP 518 deps already in
host).

## Pin-Policy Invariants

- Host pinnings: exact versions, no comparison operators — except keys in `conda_build_config.yaml` (implicit pins).
- `run_exports` on host deps auto-populates `run:`; never hand-pin what a host dep already covers.
- C/C++ libs: pin to major or `x.x`, matching upstream's run_exports.
- NumPy (C API): `numpy {{ numpy }}` in host, `pin_compatible` in run.
- `run_constrained` for conflicts (`pkg <0`) and optional features (`opt >=2.0`), never to force installs.
- Never suppress overlinking — add the missing dep. Overdepending may be suppressed with justification.

## Top-5 Common Errors

| Error                | One-line fix                                                 |
| -------------------- | ------------------------------------------------------------ |
| Hunk FAILED          | Regenerate patch against current source version              |
| Checksum mismatch    | Verify sha256 matches the downloaded tarball                 |
| UnsatisfiableError   | `conda create -n test --dry-run pkg=ver` to debug conflict   |
| Overlinking          | Add the linked library to `run:` (or upstream run_exports)   |
| ModuleNotFoundError  | Dep in wrong section (host vs run vs test/requires) or typo  |

## References

| Topic                                        | File                                                 |
| -------------------------------------------- | ---------------------------------------------------- |
| Recipe structure, noarch, multi-output, requirements, compilers | [references/recipe.md](references/recipe.md)         |
| Pinnings, run_exports, cbc.yaml, platform selectors | [references/pinnings.md](references/pinnings.md)     |
| Testing, patches                             | [references/testing-patches.md](references/testing-patches.md) |
| GPU (CUDA/Metal), OpenMP                     | [references/platforms.md](references/platforms.md)   |
| Common errors, linter rules                  | [references/errors-lint.md](references/errors-lint.md) |
| conda-build CLI, crm, verification           | [references/tools.md](references/tools.md)           |
