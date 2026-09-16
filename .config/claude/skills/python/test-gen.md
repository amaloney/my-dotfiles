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

1. **Analyze**: `Agent({ prompt: "List untested functions. Return file:func:type_needed" })`
2. **Generate (parallel)**: Different dirs = no conflict
   ```
   Agent({ prompt: "Load [[python/testing]]. Gen <type> tests for <list>. Output tests/<type>/" })
   ```
3. **Verify**: `pytest tests/ -x`

[[python/testing]] [[python/style]]
