---
name: rust
description: Rust orchestrator - routes to specialized skills
invocation: auto
extensions: [".rs"]
keywords: ["rust", "cargo"]
---

# Rust Router

Handoff: `next: done`.

## Session Start

Profile check: `test -f .harness/code_index/profile.json && find .harness/code_index/profile.json -mtime -7 | grep -q .`
Missing/stale → [[rust/recon]].

## Pre-Generation

Query: `jq '.patterns.config_rs_path, .project.workspace_members' .harness/code_index/profile.json` Search:
`python3 .harness/code_index/query.py search "<pattern>"` Similar exists → extend.

## Post-Generation

[[bug]] → [[rust/violations]] → [[rust/test-gen]]. 2 fix cycles max.

## Registry

| Skill                     | Type    | Purpose               | Triggers                                                         |
| ------------------------- | ------- | --------------------- | ---------------------------------------------------------------- |
| [[rust/recon]]            | leaf    | Profile project       | session start, profile, scan                                     |
| [[rust/repo-init]]        | leaf    | Repo bootstrap        | bootstrap, onboard, repo init, AGENTS.md                         |
| [[rust/tooling]]          | leaf    | cargo/clippy/nextest  | init, Cargo.toml, toolchain, clippy config, audit                |
| [[rust/style]]            | router  | Style router          | create, write, implement, style violations                       |
| [[rust/types]]            | leaf    | Signatures, ownership | `&str`, `impl Trait`, newtype, clone, lifetimes                  |
| [[rust/naming]]           | leaf    | Naming conventions    | variables, constants, `as_`/`to_`/`into_`                        |
| [[rust/structure]]        | leaf    | File/module layout    | `mod`, `use`, `pub`, line length                                 |
| [[rust/errors]]           | leaf    | Error handling        | `Result`, `?`, unwrap, thiserror, anyhow                         |
| [[rust/org]]              | leaf    | File organization     | config.rs, lib.rs/main.rs, consts                                |
| [[rust/security]]         | leaf    | Security patterns     | unsafe, audit, overflow, injection, secrets                      |
| [[debugging]]             | leaf    | Bug check/fix         | fix, debug, panic, backtrace                                     |
| [[rust/testing]]          | leaf    | Test core + rstest    | test, assert, nextest, fixture, doctest                          |
| [[rust/property-testing]] | leaf    | proptest              | property, proptest, fuzz                                         |
| [[rust/violations]]       | fan-out | Lint/fix (fan-out)    | fix violations, clippy, clean up, orchestrate, fan-out, parallel |
| [[rust/test-gen]]         | fan-out | Gen tests (fan-out)   | generate tests, add coverage                                     |
| [[build-watch-fix]]       | leaf    | Auto-fix loop         | build failure, auto-fix, watch                                   |

**Not yet covered** — mocking (`mockall`), async testing (`#[tokio::test]`), BDD (`cucumber`). A request for these → say
no rust skill exists yet, apply [[rust/testing]] conventions, and flag it to the user rather than improvising rules.

## Pipelines

| Task           | Chain                                                       |
| -------------- | ----------------------------------------------------------- |
| New project    | tooling (bootstrap) → style → bug → violations → test-gen   |
| New module     | style → bug → violations → test-gen                         |
| Bug fix        | debugging → test-driven-development → violations → test-gen |
| Refactor       | style → bug → violations                                    |
| Fix violations | violations                                                  |
| Generate tests | test-gen                                                    |
| Add tests      | testing                                                     |
| Property tests | property-testing                                            |

## Bug Finding

Clippy is the checker. Mapping: [[ast-check]] (`references/rust-clippy.md`).
`cargo clippy --all-targets --all-features -- -W clippy::correctness -W clippy::suspicious` Fallback:
`rg -n '\.unwrap\(\)|\.expect\(' --type rust src/`

## Principles

| Prefer                                            | Over                           |
| ------------------------------------------------- | ------------------------------ |
| Extend existing                                   | Create new                     |
| Flat/explicit                                     | Nested/clever (macro magic)    |
| 3 similar lines                                   | Premature trait/generic        |
| Borrow (`&T`)                                     | `.clone()` to appease borrowck |
| Existing deps (missing crate → stop, report name) | `cargo add` on your own        |
| `todo!()` / `unimplemented!()` for WIP            | `TODO` comments                |

## Execution

**Prescriptive** — skill first, sub-agents, no exploring.

**Orchestration**: "orchestrate"/"fan-out" OR plan ≥3 tasks → subagent-per-task with reviewers. <3 tasks or trivial →
native (state reason).

**Plan precondition**: verify tasks have pipeline stage annotations ([[writing-plans]]). Missing → annotate or return.

**Reviewers**: disprove-first. Prompt: "Assume wrong. Hunt [[rust/structure]], [[rust/naming]], [[rust/types]],
[[rust/errors]]. Report file:line." No findings → show why.

1. Task → pipeline → `Agent({ prompt: "[[rust/<skill>]] + <artifact>" })`
2. Gate: `cargo fmt --check && cargo clippy -- -D warnings` clean before test-gen
3. Pass artifacts, return after final
