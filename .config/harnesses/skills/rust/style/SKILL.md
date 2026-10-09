---
name: rust/style
description: Rust style router - routes to types, naming, structure, errors, org
invocation: auto
---

# Rust Style Router

Handoff: `next: bug`.

| Concern   | Skill               | Triggers                                       |
| --------- | ------------------- | ---------------------------------------------- |
| Types     | [[rust/types]]      | signatures, borrowing, clone, newtype, generics |
| Naming    | [[rust/naming]]     | variables, constants, conversions, getters     |
| Structure | [[rust/structure]]  | mod, use, pub, layout, line length             |
| Errors    | [[rust/errors]]     | Result, ?, unwrap, panic, thiserror, anyhow    |
| Files     | [[rust/org]]        | config.rs, lib.rs/main.rs, where to put        |
| Lint      | [[rust/violations]] | clippy, rustfmt, lint                          |

Load specific leaf for focused task. Load all for full review.

## Violation Detection

"style violations" → check both:

1. `cargo fmt --check && cargo clippy --all-targets -- -D warnings` → [[rust/violations]]
2. Review-time gates clippy cannot see: naming grep ([[rust/naming]]), `pub` minimality and sugar gate
   ([[rust/structure]])

"orchestrate" → agents per clippy lint + one for structure ([[rust/structure]] + [[rust/org]])
