# Testing & Patches

## Testing

### Minimum Test Section

```yaml
test:
  imports:
    - mypackage
  commands:
    - pip check # requires pip in test/requires
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
    - patch # [unix]
    - m2-patch # [win]
```

**Best practices**:

- Keep original author/commit info
- Link to upstream PR/issue
- Note when patch can be dropped
