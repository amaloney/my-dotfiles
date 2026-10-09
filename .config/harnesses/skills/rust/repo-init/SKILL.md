---
name: rust/repo-init
description: Bootstrap repo-level AGENTS.md + .harness profile for a Rust project
---

# Rust Repo Init

Handoff: `next: done`.

Bootstrap harness integration for a Rust repo: repo-level instructions + `.harness/` profile.

## When

User asks to set up / onboard / initialize a Rust project for harness-assisted work, or a Rust repo lacks
`AGENTS.md` / `.harness/code_index/profile.json`.

## Steps

1. Write the repo instructions below to `<repo>/AGENTS.md`. If one exists, merge — never overwrite silently.
2. Load [[rust/recon]] and run it to generate `.harness/code_index/profile.json`.
3. Ensure `.harness/` is in the repo's `.gitignore` (generated state, never committed).
4. Offer the code index: `~/.config/harnesses/skills/code-index/scripts/install.sh <repo>` (indexes `.rs` via
   tree-sitter when available).

## Repo instructions (write to AGENTS.md)

````markdown
# Project Instructions

## Session Start

1. Check `.harness/code_index/profile.json` exists and fresh (<7 days)
2. If missing/stale → run rust/recon to generate profile
3. Load the rust orchestrator skill
4. Read `README.md` and `TODO.md` (if exists) for context

```bash
test -f .harness/code_index/profile.json && \
  find .harness/code_index/profile.json -mtime -7 | grep -q . && \
  echo "CURRENT" || echo "NEEDS UPDATE"
```

## Profile (code_index/profile.json)

All skills read this instead of scanning. Contains:

- `project.type` — cli | library | webapp | proc-macro | workspace
- `project.rust_version` — MSRV; bounds allowed std APIs
- `project.workspace_members` — crates in the workspace
- `patterns.config_rs_path` — where shared constants go
- `patterns.error_crate` — thiserror | anyhow | both

```bash
jq '.project.type, .project.rust_version' .harness/code_index/profile.json
```

## Rust Workflow

| Task            | Load                                              |
| --------------- | ------------------------------------------------- |
| New code        | rust/style → rust/violations → debugging          |
| Tests           | rust/testing                                      |
| Property tests  | rust/property-testing                             |
| Bug fix         | debugging → verify with test                      |
| Security        | rust/security                                     |
| Refresh profile | rust/recon                                        |

## Rules (from profile)

- Constants → `profile.patterns.config_rs_path` (NEVER mid-function)
- Integration tests → `tests/`; unit tests → `#[cfg(test)] mod tests` beside the code
- No `unwrap()`/`expect()` outside tests

## Testing

```bash
# Targeted only — never the full suite
cargo nextest run -p <crate> -E 'test(<name>)'
cargo test -p <crate> <name>              # if nextest is not installed
```

## Tools

```bash
cargo fmt --check                                     # Format check
cargo clippy --all-targets --all-features -- -D warnings   # Lint
cargo audit                                           # Advisory DB
```
````

[[rust]] [[rust/recon]]
