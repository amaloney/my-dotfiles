---
name: python
description: Python orchestrator - routes to specialized skills
invocation: auto
---

# Python Router

## Session Start (Recon)

```bash
# Check profile exists and is fresh (<7 days)
test -f .claude/code_index/profile.json && \
  find .claude/code_index/profile.json -mtime -7 | grep -q . && \
  echo "profile: current" || echo "profile: needs update"
```

| State | Action |
|-------|--------|
| Missing | Run [[python/recon]] |
| Stale (>7 days) | Offer to refresh |
| Current | Read and use |

**After recon:** All skills read `.claude/code_index/profile.json` for project context.

## Pre-Generation

```bash
# Query profile for context
cat .claude/code_index/profile.json | jq '.patterns.config_py_path'
```

Similar exists → extend. Check `profile.patterns.config_py_path` for constants.

## Post-Generation

1. [[python/violations]] — ruff + structure
2. [[python/bugs]] — AST bugs/security
3. [[python/test-gen]] — if 1+2 pass

2 fix cycles max → report to user.

## Registry

| Skill                       | Purpose             | Triggers                                                                  |
| --------------------------- | ------------------- | ------------------------------------------------------------------------- |
| [[python/recon]]            | Profile project     | session start, profile, scan                                              |
| [[python/pixi-pyproject]]   | Pixi project setup  | init, pyproject, pixi                                                     |
| [[python/modern-tooling]]   | uv/ruff/ty setup    | uv, ruff, ty, modern, pip replace                                         |
| [[python/style]]            | Style router        | create, write, implement, style violations, structure violations          |
| [[python/types]]            | Type annotations    | `->`, Optional, Callable                                                  |
| [[python/naming]]           | Naming conventions  | variables, constants, `_`                                                 |
| [[python/structure]]        | File layout         | imports, line length                                                      |
| [[python/errors]]           | Exception handling  | try/except                                                                |
| [[python/org]]              | File organization   | config.py, utils.py                                                       |
| [[python/bugs]]             | Bug check/fix       | fix, debug, error                                                         |
| [[python/testing]]          | Pytest core         | test, pytest, assert                                                      |
| [[python/conftest]]         | Shared fixtures     | conftest, fixture, scope                                                  |
| [[python/mocking]]          | Mock patterns       | mock, patch, mocker                                                       |
| [[python/property-testing]] | Hypothesis          | property, hypothesis, fuzz                                                |
| [[python/async-testing]]    | Async tests         | async, asyncio, pytest-asyncio, await                                     |
| [[python/security]]         | Security patterns   | security, vuln, injection, crypto                                         |
| [[python/bdd]]              | Behave BDD          | behave, gherkin, bdd, feature                                             |
| [[python/violations]]       | Lint/fix (fan-out)  | fix violations, ruff violations, clean up, orchestrate, fan-out, parallel |
| [[python/test-gen]]         | Gen tests (fan-out) | generate tests, add coverage                                              |
| [[build-watch-fix]]         | Auto-fix loop       | build failure, auto-fix, watch                                            |

## Routing Tree

```
python.md (this)
├── recon              (leaf) — profile.json generation [RUN FIRST]
├── pixi-pyproject     (leaf) — pixi setup
├── modern-tooling     (leaf) — uv/ruff/ty
├── style              (router)
│   ├── types          (leaf)
│   ├── naming         (leaf)
│   ├── structure      (leaf)
│   ├── errors         (leaf)
│   └── org            (leaf)
├── bugs               (leaf) — diagnosis + patterns
├── testing            (leaf) — pytest core
├── conftest           (leaf) — shared fixtures
├── mocking            (leaf) — mock patterns
├── property-testing   (leaf) — hypothesis
├── async-testing      (leaf) — pytest-asyncio
├── security           (leaf) — vulns, insecure defaults
├── bdd                (leaf) — behave/gherkin
├── violations         (fan-out)
└── test-gen           (fan-out)
```

## Pipelines

| Task           | Chain                                                                  |
| -------------- | ---------------------------------------------------------------------- |
| New project    | pixi-pyproject → modern-tooling → style → violations → bugs → test-gen |
| New script     | style → violations → bugs → test-gen                                   |
| Bug fix        | bugs → violations → test-gen                                           |
| Refactor       | style → violations → bugs                                              |
| Fix violations | violations                                                             |
| Generate tests | test-gen                                                               |
| Add tests      | testing + conftest + mocking (as needed)                               |
| Property tests | property-testing                                                       |

## Execution

**Prescriptive** — load skill first, spawn sub-agents, no exploring:

1. Match task → pipeline
2. Each step: `Agent({ prompt: "Load [[python/<skill>]]. <task> + <artifact>" })`
3. **Gate**: violations and bugs must pass before test-gen
   - violations: `ruff check` returns clean
   - bugs: agent confirms no issues found
4. Pass artifacts between agents
5. Return after final

## Gate Logic

```
style creates artifact
  ↓
violations (fan-out) → fixes until ruff clean
  ↓
bugs → fixes until no issues
  ↓ (only if clean)
test-gen (fan-out) → creates tests
  ├── testing (pytest core)
  ├── conftest (shared fixtures)
  ├── mocking (if external deps)
  └── property-testing (if algebraic shape)
```

If violations or bugs persist after 2 fix cycles, return to user with findings.

## Skill Selection for Testing

| Code Shape                     | Skills to Load                                            |
| ------------------------------ | --------------------------------------------------------- |
| Simple unit tests              | testing                                                   |
| Tests with fixtures            | testing + conftest                                        |
| Tests with external deps       | testing + mocking                                         |
| Async code                     | testing + async-testing                                   |
| Roundtrip/invariant properties | property-testing                                          |
| Full test suite                | testing + conftest + mocking + property-testing           |
| Full async test suite          | testing + conftest + mocking + async-testing              |
