---
name: build-watch-fix
description: Autonomous loop - watch builds, detect failures, auto-fix, write tests
invocation: manual
---

# Build-Watch-Fix Loop

Autonomous cycle: build → detect failure → fix → test → rebuild.

## Loop Structure

```
while not all_succeeded:
  1. Run build
  2. Parse logs for failure pattern
  3. Match pattern → fix strategy
  4. Apply fix (extend existing code)
  5. Run [[python/violations]] → [[python/bugs]]
  6. Write test for fix
  7. Rebuild

  Gate: 3 fix attempts per failure → report to user
```

## Failure → Fix Mapping

| Pattern                  | Fix Strategy                           |
| ------------------------ | -------------------------------------- |
| `ModuleNotFoundError: X` | Add X to meta.yaml requirements        |
| `UnsatisfiableError`     | Add missing dep to resolver queue      |
| `sha256 mismatch`        | Fetch correct hash, update meta.yaml   |
| `Hunk FAILED`            | Regenerate patch from upstream         |
| `overlinking`            | Add lib to run_exports or requirements |
| Build timeout            | Increase resource limits               |

## Fix Protocol

1. **Query code_index** — find existing fix pattern
2. **Extend existing** — don't create new function if similar exists
3. **Validate** — [[python/violations]] + [[python/bugs]]
4. **Test** — write test covering the fix scenario
5. **Rebuild** — verify fix works

## Agent Orchestration

"orchestrate" → spawn per failure type:

- Agent per unique error pattern
- Each agent: diagnose → fix → test
- Coordinator aggregates results

[[python-pipeline]] [[conda-packaging]]
