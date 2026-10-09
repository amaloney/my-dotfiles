---
name: rust/structure
description: Rust file and module structure - layout, use grouping, visibility, sugar gate, docs
invocation: auto
---

# Structure

Handoff: `next: done`.

Lines ≤120 (`max_width = 120`, [[rust/tooling]]). Prefer expression-oriented flow (`match`/`if` as values) over
mutable accumulators. Early `return`/`?` is idiomatic for guard clauses and error propagation; avoid scattered
`return`s in the happy path.

## File Order (strict)

```rust
// 1. Module docs (//!)
// 2. `use` declarations (grouped, below)
// 3. `mod` declarations
// 4. Constants and statics — NEVER inside fn bodies unless truly local
// 5. Types (struct/enum) each followed by its impl blocks
// 6. Free functions
// 7. #[cfg(test)] mod tests — always last
```

**Constants:** [[rust/org]].

## Modules

- File modules: `foo.rs` + `foo/bar.rs` (2018+ layout). No new `mod.rs` files unless the crate already uses them —
  match the crate.
- One concept per module; a module that needs a `utils` submodule is usually two modules.

## `use` declarations

Three groups, blank line between, alphabetical within (rustfmt sorts within groups; grouping is a review gate):

```rust
use std::collections::HashMap;
use std::path::PathBuf;

use serde::Deserialize;

use crate::config::URL_REGISTRY;
```

Paths via `crate::`, not `super::super::`. `super::` only inside `mod tests` (`use super::*;`). No glob imports
outside tests and preludes.

## Visibility

**Default to private; widen deliberately.** Order of preference: private → `pub(crate)` → `pub`. A `pub` item is
API surface — it needs a doc comment and semver care. In binaries, `pub` buys nothing; use `pub(crate)` or private.

Review gate on every file you create or edit:

```bash
rg -n '^\s*pub (fn|struct|enum|trait|const|mod)' <file>   # each hit: is it used outside the crate? else pub(crate)
```

## Functions

**Syntactic sugar adds complexity.** A one-expression wrapper adds indirection, not abstraction. Inline it.

**Gate before creating any function:** "is this more than one expression, used more than once?" No to either → do not
create it.

| Pattern                                      | Problem                       | Fix                |
| -------------------------------------------- | ----------------------------- | ------------------ |
| `fn name(&self) -> &str { &self.name }` on a private field used only in-crate | Getter ceremony | Field access |
| `fn normalize(s: &str) -> String { s.trim().to_lowercase() }` used once | Single-use, single expression | Inline + why-comment |
| Trait with one impl "for testing"            | Sugar at type level           | Concrete type      |
| `macro_rules!` for a pattern used twice      | Macro magic                   | Function or inline |

**When to extract:** reused 3+ times, OR the name documents non-obvious intent, OR the expression obscures the caller.

## Call sites

Rust has no keyword arguments — readability comes from types. Bare `bool`/`Option` literals at call sites
(`connect(true, None, false)`) → replace with an enum or a builder / options struct
(`connect(Mode::Tls, Retry::default())`). A function taking >4 parameters gets a params struct.

**Never guess an API.** Read the real signature before calling: rust-analyzer hover, `cargo doc --open -p <crate>`,
or the source under `~/.cargo/registry/src/`. The compiler catches wrong types, not wrong *semantics* of similarly
typed parameters (`(width, height)` vs `(height, width)`) — newtypes ([[rust/types]]) close that gap.

## Comments and docs

Comments only when WHY is non-obvious. No tombstones, no decorative banners.

Every `pub` item gets a `///` doc comment written with the signature: one summary line, then `# Errors` for
`Result`-returning fns, `# Panics` if it can panic, `# Safety` for `unsafe fn`. Examples in docs are doctests — they
must compile and run ([[rust/testing]]).

[[rust/org]] [[rust/types]]
