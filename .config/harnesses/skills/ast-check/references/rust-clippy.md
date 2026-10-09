# Rust: ast-check groups → clippy

No custom AST checker for Rust — rustc + clippy already parse and type-check, so each ast-check group maps to lint
groups and individual lints. Use from [[rust]] (Bug Finding), [[bug]] (Rust logic pass), [[debugging]] (Phase 0).

## Mapping

| ast-check group | Clippy / rustc lints                                                                                     |
| --------------- | -------------------------------------------------------------------------------------------------------- |
| `bugs`          | groups `clippy::correctness`, `clippy::suspicious`; rustc `unused_must_use`, `unreachable_code`; `clippy::let_underscore_must_use`, `clippy::unwrap_in_result`, `clippy::float_cmp` |
| `security`      | rustc `unsafe_code`; `clippy::undocumented_unsafe_blocks`, `unwrap_used`, `expect_used`, `panic`, `indexing_slicing`, `arithmetic_side_effects`, `cast_possible_truncation`, `string_slice`, `mem_forget` |
| `quality`       | groups `clippy::complexity`, `clippy::perf`; `cognitive_complexity`, `too_many_lines`, `too_many_arguments`, `excessive_nesting` (needs `clippy.toml` threshold), `needless_pass_by_value`, `redundant_clone`, `unused_self` |
| `structure`     | `clippy::items_after_statements`, `items_after_test_module`, `mod_module_files` (bans `mod.rs`) or `self_named_module_files` (bans `foo.rs` + `foo/`) — pick the one matching [[rust/structure]] |
| `underscore`    | `clippy::used_underscore_binding`, `used_underscore_items` (a `_name` that is actually used)             |
| `undefined`     | the compiler — unresolved names don't build                                                              |

## One-shot run (no Cargo.toml edits)

```bash
cargo clippy --all-targets --all-features --message-format=short -- \
  -W clippy::correctness -W clippy::suspicious \
  -W clippy::unwrap_used -W clippy::expect_used -W clippy::indexing_slicing -W clippy::undocumented_unsafe_blocks \
  -W clippy::cognitive_complexity -W clippy::too_many_lines \
  -W clippy::items_after_statements -W clippy::used_underscore_binding
```

Exit-1-on-error equivalent: append `-D warnings`. Machine-readable: `--message-format=json` (jq recipe in
[[rust/violations]]).

## Persistent config

```toml
# Cargo.toml (or [workspace.lints.clippy] + `[lints] workspace = true` in members)
[lints.rust]
unsafe_code = "forbid"

[lints.clippy]
correctness = { level = "deny", priority = -1 }
suspicious = { level = "warn", priority = -1 }
complexity = { level = "warn", priority = -1 }
perf = { level = "warn", priority = -1 }
unwrap_used = "warn"
expect_used = "warn"
indexing_slicing = "warn"
undocumented_unsafe_blocks = "warn"
cognitive_complexity = "warn"
too_many_lines = "warn"
items_after_statements = "warn"
used_underscore_binding = "warn"
```

```toml
# clippy.toml
cognitive-complexity-threshold = 10       # matches ast-check's cyclomatic >10
too-many-lines-threshold = 80
excessive-nesting-threshold = 4           # matches ast-check's nesting >4
allow-unwrap-in-tests = true
allow-expect-in-tests = true
allow-indexing-slicing-in-tests = true
```

Lint names drift between clippy releases (lints move groups or get renamed) — `cargo clippy --explain <lint>` and
`unknown_lints` warnings are the source of truth for the installed toolchain.
