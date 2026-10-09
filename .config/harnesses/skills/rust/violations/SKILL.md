---
name: rust/violations
description: Fan-out detect/fix Rust violations using rustfmt + clippy with Cargo.toml [lints]
invocation: manual
---

# Violations Fixer

Handoff: `next: rust/testing`.

## Detection

Lints come from `Cargo.toml` `[lints]` / `[workspace.lints]` (config: [[rust/tooling]]).

```bash
cargo fmt --check                                                     # format (always fix first, mechanically)
cargo clippy --all-targets --all-features --message-format=json 2>/dev/null \
  | jq -r 'select(.reason == "compiler-message") | .message
           | select(.code != null)
           | [.code.code, .level, (.spans[0] | "\(.file_name):\(.line_start)"), .message] | @tsv' \
  | sort -u                                                           # lint<TAB>level<TAB>file:line<TAB>message
cargo clippy --all-targets --all-features                             # human readable
```

Group by the first column (lint name, e.g. `clippy::needless_borrow`, `unused_imports`).

## Execution Mode

| Request                                  | Action                                                       |
| ---------------------------------------- | ------------------------------------------------------------ |
| "orchestrate"/"fan-out"/"parallel"       | Spawn agents per lint — no `clippy --fix` shortcut           |
| "fix violations" (no approach specified) | <5 distinct lints → `cargo clippy --fix`; else agents        |

## Protocol

1. **Format**: `cargo fmt` — mechanical, never delegated
2. **Detect**: clippy JSON above → group by lint name
3. **Fix (sequential by lint)**: for each lint with findings:
   ```
   Agent({ prompt: "Load [[rust/style]]. Fix ONLY <lint> findings. Re-read before edit. <findings>" })
   ```
4. **Auto-fix machine-applicable lints**: `cargo clippy --fix --allow-dirty --all-targets` (only if user didn't
   request agents)
5. **Verify**: `cargo fmt --check && cargo clippy --all-targets --all-features -- -D warnings` — must be clean

Sequential fixes by lint prevent overwrite conflicts. `#[allow(clippy::...)]` is a fix only with a same-line comment
saying why the lint is wrong here; prefer `#[expect(...)]` (1.81+) so the suppression errors once it is stale.

## Common Lints

| Lint                             | Issue                                         |
| -------------------------------- | --------------------------------------------- |
| `unused_*` / `dead_code`         | rustc: unused imports, vars, items            |
| `clippy::needless_borrow`        | `&` on something already a reference          |
| `clippy::redundant_clone`        | clone of a value never used again             |
| `clippy::unwrap_used`            | panic path outside tests ([[rust/errors]])    |
| `clippy::too_many_arguments`     | >7 params → params struct ([[rust/structure]]) |
| `clippy::needless_pass_by_value` | owned param only borrowed ([[rust/types]])    |
| `clippy::module_name_repetitions` | `config::ConfigError` stutter (pedantic)     |

[[rust/style]] [[debugging]]
