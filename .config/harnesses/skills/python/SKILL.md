---
name: python
description: Python orchestrator - routes to specialized skills
invocation: auto
extensions: [".py"]
keywords: ["python"]
---

# Python Router

Handoff: `next: done`.

## MANDATORY: Post-Generation Pipeline

**NEVER skip this after ANY code creation.** Skipping is a skill violation.

After writing Python code, you MUST:

1. Run: `style-gates.sh <modified-files>` — paste output as evidence
2. Launch subagent for [[bug]] stage (fan-out to audit sub-subagents)
3. Launch subagent for [[python/violations]] stage (lint/fix enforcement)
4. Launch subagent for [[python/test-gen]] stage (if tests needed)

Max 2 fix cycles. Gate must pass before test-gen.

---

## Session Start

Profile check: `test -f .harness/code_index/profile.json && find .harness/code_index/profile.json -mtime -7 | grep -q .`
Missing/stale → [[python/recon]].

## Pre-Generation

Query profile: `jq '.patterns.config_py_path' .harness/code_index/profile.json` Search:
`python3 .harness/code_index/query.py search "<pattern>"` Similar exists → extend.

## Post-Generation

1. `style-gates.sh <paths>` — paste output as evidence
2. [[bug]] → [[python/violations]] → [[python/test-gen]]

2 fix cycles max.

## Registry

| Skill                       | Type    | Purpose             | Triggers                                                                  |
| --------------------------- | ------- | ------------------- | ------------------------------------------------------------------------- |
| [[python/recon]]            | leaf    | Profile project     | session start, profile, scan                                              |
| [[python/repo-init]]        | leaf    | Repo bootstrap      | bootstrap, onboard, repo init, AGENTS.md                                  |
| [[python/pixi-pyproject]]   | leaf    | Pixi project setup  | init, pyproject, pixi                                                     |
| [[python/modern-tooling]]   | leaf    | uv/ruff/ty setup    | uv, ruff, ty, modern, pip replace                                         |
| [[python/style]]            | router  | Style router        | create, write, implement, style violations, structure violations          |
| [[python/types]]            | leaf    | Type annotations    | `->`, Optional, Callable                                                  |
| [[python/naming]]           | leaf    | Naming conventions  | variables, constants, `_`                                                 |
| [[python/structure]]        | leaf    | File layout         | imports, line length                                                      |
| [[python/errors]]           | leaf    | Exception handling  | try/except                                                                |
| [[python/org]]              | leaf    | File organization   | config.py, utils.py                                                       |
| [[debugging]]               | leaf    | Bug check/fix       | fix, debug, error                                                         |
| [[python/testing]]          | leaf    | Pytest core         | test, pytest, assert                                                      |
| [[python/conftest]]         | leaf    | Shared fixtures     | conftest, fixture, scope                                                  |
| [[python/mocking]]          | leaf    | Mock patterns       | mock, patch, mocker                                                       |
| [[python/property-testing]] | leaf    | Hypothesis          | property, hypothesis, fuzz                                                |
| [[python/async-testing]]    | leaf    | Async tests         | async, asyncio, pytest-asyncio, await                                     |
| [[python/security]]         | leaf    | Security patterns   | security, vuln, injection, crypto                                         |
| [[python/bdd]]              | leaf    | Behave BDD          | behave, gherkin, bdd, feature                                             |
| [[python/violations]]       | fan-out | Lint/fix (fan-out)  | fix violations, ruff violations, clean up, orchestrate, fan-out, parallel |
| [[python/test-gen]]         | fan-out | Gen tests (fan-out) | generate tests, add coverage                                              |
| [[build-watch-fix]]         | leaf    | Auto-fix loop       | build failure, auto-fix, watch                                            |

## Pipelines

| Task           | Chain                                                                             |
| -------------- | --------------------------------------------------------------------------------- |
| New project    | pixi-pyproject + modern-tooling (bootstrap) → style → bug → violations → test-gen |
| New script     | style → bug → violations → test-gen                                               |
| Bug fix        | debugging → test-driven-development → violations → test-gen                       |
| Refactor       | style → bug → violations                                                          |
| Fix violations | violations                                                                        |
| Generate tests | test-gen                                                                          |
| Add tests      | testing + conftest + mocking (as needed)                                          |
| Property tests | property-testing                                                                  |

Test-type skill selection: [[python/test-gen]].

## Bug Finding

`ast_checker.py src/` or `rg -n "\._[a-z][a-z_]+\(" --type py src/`

## Principles

| Prefer                                                   | Over                  |
| -------------------------------------------------------- | --------------------- |
| Extend existing                                          | Create new            |
| Flat/explicit                                            | Nested/clever         |
| 3 similar lines                                          | Premature abstraction |
| Active environment (missing package → stop, report name) | Installing packages   |
| `NotImplementedError` for WIP                            | `TODO` comments       |

## Execution

**Prescriptive** — skill first, sub-agents, no exploring.

**Orchestration**: "orchestrate"/"fan-out" OR plan ≥3 tasks → subagent-per-task with reviewers. <3 tasks or trivial →
native (state reason).

**Plan precondition**: verify tasks have pipeline stage annotations ([[writing-plans]]). Missing → annotate or return.

**Reviewers**: disprove-first. Prompt: "Assume wrong. Hunt [[python/structure]], [[python/naming]], [[python/errors]].
Run `style-gates.sh`, report file:line." No findings → show gate output.

1. Task → pipeline → `Agent({ prompt: "[[python/<skill>]] + <artifact>" })`
2. Gate: violations + bugs clean before test-gen
3. Pass artifacts, return after final
