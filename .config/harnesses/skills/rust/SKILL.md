---
name: rust
description: Rust orchestrator - routes to specialized skills
invocation: auto
extensions: [".rs"]
keywords: ["rust", "cargo"]
---

# Rust Router

Handoff: `next: done`.

## Session Start (Recon)

```bash
# Check profile exists and is fresh (<7 days)
test -f .harness/code_index/profile.json && \
  find .harness/code_index/profile.json -mtime -7 | grep -q . && \
  echo "profile: current" || echo "profile: needs update"
```

Missing or stale → run [[rust/recon]]. Profile consumed by all rust skills.

## Pre-Generation

```bash
# Query profile for context
jq '.patterns.config_rs_path, .project.workspace_members' .harness/code_index/profile.json

# Search indexed code for existing implementations
python3 .harness/code_index/query.py search "<pattern>"   # If code index exists
```

Similar exists → extend. Check `profile.patterns.config_rs_path` for constants.

## Post-Generation

1. [[bug]] — audit (logic, edge/IO/security)
2. [[rust/violations]] — rustfmt + clippy
3. [[rust/test-gen]] — if 1+2 pass

2 fix cycles max → report to user.

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

**Not yet covered** — mocking (`mockall`), async testing (`#[tokio::test]`), BDD (`cucumber`). A request for these →
say no rust skill exists yet, apply [[rust/testing]] conventions, and flag it to the user rather than improvising rules.

## Pipelines

| Task           | Chain                                                              |
| -------------- | ------------------------------------------------------------------ |
| New project    | tooling (bootstrap) → style → bug → violations → test-gen          |
| New module     | style → bug → violations → test-gen                                |
| Bug fix        | debugging → test-driven-development → violations → test-gen        |
| Refactor       | style → bug → violations                                           |
| Fix violations | violations                                                         |
| Generate tests | test-gen                                                           |
| Add tests      | testing                                                            |
| Property tests | property-testing                                                   |

## Bug Finding

No custom AST checker for Rust — clippy is the checker. Lint-group mapping: [[ast-check]] (`references/rust-clippy.md`).

```bash
cargo clippy --all-targets --all-features --message-format=short -- -W clippy::correctness -W clippy::suspicious
rg -n '\.unwrap\(\)|\.expect\(' --type rust src/       # Fallback: panics outside tests
```

## Principles

| Prefer                                                   | Over                          |
| -------------------------------------------------------- | ----------------------------- |
| Extend existing                                          | Create new                    |
| Flat/explicit                                            | Nested/clever (macro magic)   |
| 3 similar lines                                          | Premature trait/generic       |
| Borrow (`&T`)                                            | `.clone()` to appease borrowck |
| Existing deps (missing crate → stop, report name)        | `cargo add` on your own       |
| `todo!()` / `unimplemented!()` for WIP                   | `TODO` comments               |

## Execution

**Prescriptive** — load skill first, spawn sub-agents, no exploring.

**Orchestration triggers**: "orchestrate", "fan-out", OR "implement/execute this plan" where the plan has
≥3 tasks. Plan execution defaults to subagent-per-task with reviewer gates unless the user explicitly
chose native. Native is the exception for <3-task plans or trivial diffs — state the choice and reason
before starting.

**Plan-execution precondition** — before executing an approved plan, verify each task names its pipeline
stage ([[writing-plans]] stage annotations). Stages missing → annotate the plan from the Pipelines table
first, or hand it back through [[writing-plans]]. Plan approval is never license to skip stages.

**Reviewer agents apply the AGENTS.md disprove-first invariant.** Prompt every reviewer with: "Assume
this change is wrong. Hunt for violations of [[rust/structure]] (sugar gate, `pub` minimality),
[[rust/naming]] (cryptic abbreviations — run the naming grep gate), [[rust/types]] (gratuitous clones, owned params),
and [[rust/errors]] (unwrap/expect outside tests). Report findings with file:line." A reviewer that finds nothing
must say why each gate was checked, not just "looks good".

1. Match task → pipeline
2. Each step: `Agent({ prompt: "Load [[rust/<skill>]]. <task> + <artifact>" })`
3. **Gate**: violations and bugs must pass before test-gen
   - violations: `cargo fmt --check && cargo clippy --all-targets -- -D warnings` returns clean
   - bugs: agent confirms no issues found
4. Pass artifacts between agents
5. Return after final
