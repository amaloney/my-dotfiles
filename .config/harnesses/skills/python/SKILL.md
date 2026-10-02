---
name: python
description: Python orchestrator - routes to specialized skills
invocation: auto
---

# Python Router

## Session Start (Recon)

```bash
# Check profile exists and is fresh (<7 days)
test -f .harness/code_index/profile.json && \
  find .harness/code_index/profile.json -mtime -7 | grep -q . && \
  echo "profile: current" || echo "profile: needs update"
```

Missing or stale → run [[python/recon]]. Profile consumed by all python skills.

## Pre-Generation

```bash
# Query profile for context
cat .harness/code_index/profile.json | jq '.patterns.config_py_path'

# Search indexed code for existing implementations
python3 .harness/code_index/query.py func "<pattern>"     # If code index exists
```

Similar exists → extend. Check `profile.patterns.config_py_path` for constants.

## Post-Generation

1. [[python/violations]] — ruff + structure
2. [[debugging]] — AST bugs/security
3. [[python/test-gen]] — if 1+2 pass

2 fix cycles max → report to user.

## Registry

| Skill                       | Type    | Purpose             | Triggers                                                                  |
| --------------------------- | ------- | ------------------- | ------------------------------------------------------------------------- |
| [[python/recon]]            | leaf    | Profile project     | session start, profile, scan                                              |
| [[python/pixi-pyproject]]   | leaf    | Pixi project setup  | init, pyproject, pixi                                                     |
| [[python/modern-tooling]]   | leaf    | uv/ruff/ty setup    | uv, ruff, ty, modern, pip replace                                         |
| [[python/style]]            | router  | Style router        | create, write, implement, style violations, structure violations          |
| [[python/types]]            | leaf    | Type annotations    | `->`, Optional, Callable                                                  |
| [[python/naming]]           | leaf    | Naming conventions  | variables, constants, `_`                                                 |
| [[python/structure]]        | leaf    | File layout         | imports, line length                                                      |
| [[python/errors]]           | leaf    | Exception handling  | try/except                                                                |
| [[python/org]]              | leaf    | File organization   | config.py, utils.py                                                       |
| [[debugging]]             | leaf    | Bug check/fix       | fix, debug, error                                                         |
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

| Task           | Chain                                                                  |
| -------------- | ---------------------------------------------------------------------- |
| New project    | pixi-pyproject → modern-tooling → style → violations → debugging → test-gen |
| New script     | style → violations → debugging → test-gen                                   |
| Bug fix        | debugging → test-driven-development → violations → test-gen                                           |
| Refactor       | style → violations → debugging                                         |
| Fix violations | violations                                                             |
| Generate tests | test-gen                                                               |
| Add tests      | testing + conftest + mocking (as needed)                               |
| Property tests | property-testing                                                       |

Test-type skill selection: [[python/test-gen]].

## Bug Finding

```bash
python3 ~/.config/harnesses/skills/ast-check/scripts/ast_checker.py src/
rg -n "\._[a-z][a-z_]+\(" --type py src/               # Fallback
```

## Principles

| Prefer                         | Over                                                            |
| ------------------------------ | --------------------------------------------------------------- |
| Extend existing                | Create new                                                      |
| Flat/explicit                  | Nested/clever                                                   |
| 3 similar lines                | Premature abstraction                                           |
| Active environment (missing package → stop, report name) | Installing packages                 |
| `NotImplementedError` for WIP  | `TODO` comments                                                 |

## Execution

**Prescriptive** — load skill first, spawn sub-agents, no exploring.

**Orchestration triggers**: "orchestrate", "fan-out", OR "implement/execute this plan" where the plan has
≥3 tasks. Plan execution defaults to subagent-per-task with reviewer gates unless the user explicitly
chose native. Native is the exception for <3-task plans or trivial diffs — state the choice and reason
before starting.

**Reviewer agents are antagonistic.** A reviewer's job is to reject, not approve. Prompt every reviewer
with: "Assume this change is wrong. Hunt for violations of [[python/structure]] (sugar gate, constants
placement), [[python/naming]] (underscore misuse), and [[python/errors]] (exit shape). Report findings
with file:line; approval is the failure mode when issues exist." Rubber-stamping is the failure being
prevented — a reviewer that finds nothing must say why each gate was checked, not just "looks good".

1. Match task → pipeline
2. Each step: `Agent({ prompt: "Load [[python/<skill>]]. <task> + <artifact>" })`
3. **Gate**: violations and bugs must pass before test-gen
   - violations: `ruff check` returns clean
   - bugs: agent confirms no issues found
4. Pass artifacts between agents
5. Return after final
