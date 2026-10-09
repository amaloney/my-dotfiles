---
name: rust/test-gen
description: Fan-out generate Rust unit/integration/regression/property tests
invocation: manual
---

# Test Generator

Handoff: `next: verify`.

## Types

| Type        | Location                              | Focus                                    |
| ----------- | ------------------------------------- | ---------------------------------------- |
| unit        | `#[cfg(test)] mod tests` in the source file | Single fn, private helpers, edge cases |
| integration | `tests/<area>.rs`                     | Public API, component interactions, real IO in `TempDir` |
| regression  | `tests/regression.rs`                 | Bug reproductions, one `#[test]` per issue |
| property    | `mod tests` or `tests/properties.rs`  | proptest roundtrip/invariant             |

## Protocol

1. **Analyze**: `Agent({ prompt: "List untested pub and pub(crate) fns. Return file:fn:type_needed:shape" })`
   - shape: `unit` | `integration` | `property` (roundtrip/invariant)
2. **Generate (parallel by file ownership)**: integration/regression agents write separate `tests/*.rs` files → no
   conflict. Unit tests edit source files → **one agent per source file**, never two agents on the same file.
   ```
   Agent({ prompt: "Load [[rust/testing]]. Gen <type> tests for <list>. Output <location>" })
   ```
3. **Property tests** (if algebraic shapes found):
   ```
   Agent({ prompt: "Load [[rust/property-testing]]. Gen property tests for <roundtrip/invariant fns>" })
   ```
4. **Verify**: `cargo nextest run -p <crate>` then `cargo test -p <crate> --doc`; `cargo clippy --all-targets` must
   stay clean (test code is linted too).

New dev-dependencies (`rstest`, `proptest`, `tempfile`) → stop and report to the user; do not `cargo add` unprompted.

## Skill Loading by Test Type

| Test Type   | Load Skills                      |
| ----------- | -------------------------------- |
| unit        | testing                          |
| integration | testing                          |
| regression  | testing + debugging              |
| property    | property-testing + testing       |

[[rust/testing]] [[rust/property-testing]] [[rust/style]] [[debugging]]
