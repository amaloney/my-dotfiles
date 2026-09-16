---
name: python/test-gen
description: Fan-out generate unit/integration/regression tests
invocation: manual
---

# Test Generator

## Types

| Type        | Dir                  | Focus                                |
| ----------- | -------------------- | ------------------------------------ |
| unit        | `tests/unit/`        | Single func, mocked deps, hypothesis |
| integration | `tests/integration/` | Component interactions, real deps    |
| regression  | `tests/regression/`  | Bug reproductions                    |

## Protocol

1. **Analyze**: `Agent({ prompt: "List untested functions. Return file:func:type_needed:shape" })`
   - shape: `unit` | `mock` | `property` (roundtrip/invariant)
2. **Generate (parallel)**: Different dirs = no conflict
   ```
   Agent({ prompt: "Load [[python/testing]] + [[python/conftest]]. Gen <type> tests for <list>. Output tests/<type>/" })
   ```
3. **Property tests** (if algebraic shapes found):
   ```
   Agent({ prompt: "Load [[python/property-testing]]. Gen property tests for <roundtrip/invariant funcs>" })
   ```
4. **Mock tests** (if external deps):
   ```
   Agent({ prompt: "Load [[python/mocking]]. Gen tests for <funcs with external deps>" })
   ```
5. **Verify**: `pytest tests/ -x`

## Skill Loading by Test Type

| Test Type   | Load Skills                                 |
| ----------- | ------------------------------------------- |
| unit        | testing + conftest                          |
| integration | testing + conftest + mocking                |
| regression  | testing + conftest                          |
| property    | property-testing + testing                  |

[[python/testing]] [[python/conftest]] [[python/mocking]] [[python/property-testing]] [[python/style]]
