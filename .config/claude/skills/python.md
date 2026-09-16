---
name: python
description: Python orchestrator - routes to specialized skills
invocation: auto
---

# Python Router

## Registry

| Skill                        | Purpose               | Triggers                          |
| ---------------------------- | --------------------- | --------------------------------- |
| [[python/pixi-pyproject]]    | Pixi project setup    | init, pyproject, pixi             |
| [[python/modern-tooling]]    | uv/ruff/ty setup      | uv, ruff, ty, modern, pip replace |
| [[python/style]]             | Style router          | create, write, implement          |
| [[python/types]]             | Type annotations      | `->`, Optional, Callable          |
| [[python/naming]]            | Naming conventions    | variables, constants, `_`         |
| [[python/structure]]         | File layout           | imports, line length              |
| [[python/errors]]            | Exception handling    | try/except                        |
| [[python/org]]               | File organization     | config.py, utils.py               |
| [[python/bugs]]              | Bug check/fix         | fix, debug, error                 |
| [[python/testing]]           | Pytest core           | test, pytest, assert              |
| [[python/conftest]]          | Shared fixtures       | conftest, fixture, scope          |
| [[python/mocking]]           | Mock patterns         | mock, patch, mocker               |
| [[python/property-testing]]  | Hypothesis            | property, hypothesis, fuzz        |
| [[python/security]]          | Security patterns     | security, vuln, injection, crypto |
| [[python/bdd]]               | Behave BDD            | behave, gherkin, bdd, feature     |
| [[python/violations]]        | Lint/fix (fan-out)    | fix violations, clean up          |
| [[python/test-gen]]          | Gen tests (fan-out)   | generate tests, add coverage      |

## Routing Tree

```
python.md (this)
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
├── security           (leaf) — vulns, insecure defaults
├── bdd                (leaf) — behave/gherkin
├── violations         (fan-out)
└── test-gen           (fan-out)
```

## Pipelines

| Task             | Chain                                                      |
| ---------------- | ---------------------------------------------------------- |
| New project      | pixi-pyproject → modern-tooling → style → violations → bugs → test-gen |
| New script       | style → violations → bugs → test-gen                       |
| Bug fix          | bugs → violations → test-gen                               |
| Refactor         | style → violations → bugs                                  |
| Fix violations   | violations                                                 |
| Generate tests   | test-gen                                                   |
| Add tests        | testing + conftest + mocking (as needed)                   |
| Property tests   | property-testing                                           |

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

| Code Shape                     | Skills to Load                            |
| ------------------------------ | ----------------------------------------- |
| Simple unit tests              | testing                                   |
| Tests with fixtures            | testing + conftest                        |
| Tests with external deps       | testing + mocking                         |
| Roundtrip/invariant properties | property-testing                          |
| Full test suite                | testing + conftest + mocking + property-testing |
