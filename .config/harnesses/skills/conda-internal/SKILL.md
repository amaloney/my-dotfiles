---
name: conda-internal
description: Anaconda-internal tooling - aggregate, PBP, linter, AnacondaRecipes
invocation: auto
---

# Anaconda-Internal (Not Public Conda)

Handoff: `next: done`.

## Aggregate Repository

Anaconda maintains `aggregate` repo:

- Global `conda_build_config.yaml` with standard pins
- Submodules for all feedstocks
- Run `conda build` from aggregate root to use global cbc

## Feedstock Structure

```
<package>-feedstock/
├── recipe/
│   ├── meta.yaml
│   ├── build.sh
│   ├── bld.bat
│   └── conda_build_config.yaml  # optional local overrides
├── ci_support/
└── README.md
```

## Package Build Platform (PBP)

Internal CI/CD:

- Taskcluster workers for linux-64, linux-aarch64, osx-arm64, win-64
- Release API for build management
- Channel staging before release
- Supports CUDA builds

## anaconda-linter

See [[conda-anaconda-tools]] for conda-lint usage and skip-lints.

## AnacondaRecipes

GitHub org hosting feedstocks. Often forked from conda-forge with:

- Different pinnings
- Build number alignment
- Recipe modifications for defaults channel
