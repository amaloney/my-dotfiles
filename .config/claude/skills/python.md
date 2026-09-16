---
name: python
description: Python orchestrator - routes to specialized agents
invocation: auto
---

# Python Router

## Registry

| Skill | Purpose | Triggers |
|-------|---------|----------|
| [[python/pixi-pyproject]] | Project setup | init, pyproject, pixi |
| [[python/style]] | Style router | create, write, implement |
| [[python/types]] | Type annotations | `->`, Optional, Callable |
| [[python/naming]] | Naming conventions | variables, constants, `_` |
| [[python/structure]] | File layout | imports, line length |
| [[python/errors]] | Exception handling | try/except |
| [[python/org]] | File organization | config.py, utils.py |
| [[python/bugs]] | Bug check/fix | fix, debug, error |
| [[python/testing]] | Test patterns | test, pytest |
| [[python/violations]] | Lint/fix (fan-out) | fix violations, clean up |
| [[python/test-gen]] | Gen tests (fan-out) | generate tests, add coverage |

## Pipelines

| Task | Chain |
|------|-------|
| New project | pixi-pyproject → style → violations → bugs → test-gen |
| New script | style → violations → bugs → test-gen |
| Bug fix | bugs → violations → test-gen |
| Refactor | style → violations → bugs |
| Fix violations | violations |
| Generate tests | test-gen |

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
```

If violations or bugs persist after 2 fix cycles, return to user with findings.
