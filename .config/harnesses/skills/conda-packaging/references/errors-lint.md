# Common Errors & Linter

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

| Rule                                | Fix                                         |
| ----------------------------------- | ------------------------------------------- |
| `missing_build_number`              | Add `build/number`                          |
| `compilers_must_be_in_build`        | Move `{{ compiler() }}` to `build:` section |
| `build_tools_must_be_in_build`      | Move cmake/make/git to `build:` section     |
| `host_section_needs_exact_pinnings` | Use exact versions, not ranges              |
| `missing_hash`                      | Add `sha256:` to source                     |
| `invalid_spdx_expression`           | Use valid SPDX license identifier           |
| `missing_pip_check`                 | Add `pip check` to test commands            |
| `pip_install_args`                  | Use `--no-deps --no-build-isolation`        |
| `deprecated_python_install_command` | Replace `setup.py install` with pip         |
