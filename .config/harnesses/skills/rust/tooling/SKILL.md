---
name: rust/tooling
description: Rust tooling - rustup toolchain, cargo, rustfmt, clippy lints, nextest, audit/deny
invocation: auto
keywords: ["cargo", "clippy", "rustfmt", "nextest", "Cargo.toml"]
---

# Rust Tooling

Handoff: `next: rust/style`.

## Tool Mapping

| Concern          | Tool                                      | Python analogue        |
| ---------------- | ----------------------------------------- | ---------------------- |
| Toolchain pin    | `rust-toolchain.toml` (rustup)            | `requires-python`      |
| Deps + build     | `cargo add` / `cargo build`               | uv                     |
| Format           | `cargo fmt` (rustfmt)                     | ruff format            |
| Lint             | `cargo clippy`                            | ruff check             |
| Types            | the compiler                              | ty                     |
| Test runner      | `cargo nextest run` (fallback `cargo test`) | pytest               |
| Vuln advisories  | `cargo audit`                             | pip-audit              |
| License/ban/dupe | `cargo deny check`                        | —                      |
| Unused deps      | `cargo machete`                           | deptry                 |
| Task runner      | `just` or `cargo xtask`                   | pixi tasks             |

## Commands

```bash
cargo fmt --check                                          # CI format gate
cargo clippy --all-targets --all-features -- -D warnings   # lint gate (warnings fail)
cargo clippy --fix --allow-dirty --all-targets             # auto-fix machine-applicable lints
cargo nextest run                                          # tests (doctests: cargo test --doc)
cargo audit && cargo deny check                            # supply chain
cargo machete                                              # unused dependencies
```

## Toolchain

```toml
# rust-toolchain.toml
[toolchain]
channel = "1.90"            # pin a version; "stable" only for apps that track latest
components = ["rustfmt", "clippy"]
```

Set `rust-version` (MSRV) in `Cargo.toml` for libraries; it bounds which std APIs are allowed.

## Lints in Cargo.toml

Lint config lives in `Cargo.toml`, not `#![warn(...)]` attributes scattered across crate roots. Workspaces declare
once in `[workspace.lints]` and members opt in with `[lints] workspace = true`.

```toml
[lints.rust]
unsafe_code = "forbid"
missing_docs = "warn"           # libraries only

[lints.clippy]
pedantic = { level = "warn", priority = -1 }
unwrap_used = "warn"
expect_used = "warn"
module_name_repetitions = "allow"
must_use_candidate = "allow"
```

Group levels need `priority = -1` so individual lint overrides win. Ast-check-equivalent lint selection:
[[ast-check]] (`references/rust-clippy.md`).

## rustfmt.toml

```toml
max_width = 120                 # matches the harness 120-column rule
edition = "2024"
```

Import grouping (`group_imports = "StdExternalCrate"`) is nightly-only — enforce it in review instead
([[rust/structure]]).

## Dependencies

Caret requirements with a real floor (`serde = "1.0.200"`), never `"*"`. `Cargo.lock` is the reproducibility layer —
commit it for binaries and workspaces. Feature-gate optional heavy deps (`default-features = false` + explicit
features). Missing crate in the active project → stop and report the name; do not `cargo add` unprompted.

[[rust/style]] [[rust/security]]
