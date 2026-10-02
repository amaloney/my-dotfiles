---
name: debugging
description: Bug diagnosis methodology - feedback loop, reproduce, hypothesise, instrument, fix, cleanup
invocation: auto
adapted-from: obra/superpowers v6.4.2 (MIT)
---

# Debugging

Skip phases only when explicitly justified.

## Iron Law

No fixes without root-cause investigation. Symptom fixes are failure. Applies especially when:
time-pressured, fix "seems obvious", previous fix failed, issue seems simple.

| Excuse | Reality |
| --- | --- |
| "Simple bug, skip process" | Simple bugs have root causes too |
| "Emergency, no time" | Systematic is faster than thrashing |
| "Multiple fixes at once" | Can't isolate what worked |
| "One more fix" (2+ failed) | 3 failures = architecture problem, not bad luck |

## Phase 0 — Triage

Cheap static checks before building a loop:

```bash
# Python
python3 ~/.config/harnesses/skills/ast-check/scripts/ast_checker.py --check bugs src/
python3 .harness/code_index/query_temporal.py impact <suspect_function>   # if index exists
```

## Phase 1 — Build Feedback Loop

**The skill.** Fast, deterministic, pass/fail signal = bug found. No loop = no progress.

| Priority | Method                                          |
| -------- | ----------------------------------------------- |
| 1        | Failing test (unit/integration/e2e)             |
| 2        | Curl/HTTP script against dev server             |
| 3        | CLI invocation + diff against snapshot          |
| 4        | Headless browser (Playwright/Puppeteer)         |
| 5        | Replay captured trace/payload                   |
| 6        | Throwaway harness (minimal subset, mocked deps) |
| 7        | Property/fuzz loop (1000 random inputs)         |
| 8        | Bisection harness (`git bisect run`)            |

**Iterate**: faster? sharper signal? more deterministic? 2s deterministic > 30s flaky.

**Non-deterministic**: Loop 100×, parallelise, add stress. Raise repro rate until debuggable. Snapshot the failing
environment into `.scratch/debug-<task>/env.txt` (env vars, dependency versions from active env, input payload) so the
repro survives the session.

**Cannot build loop?** Stop. List what tried. Ask user for: env access, captured artifact, or prod instrumentation
permission.

## Phase 2 — Reproduce

- [ ] Failure matches **user's** description (not nearby different bug)
- [ ] Reproducible across runs (or high enough rate)
- [ ] Exact symptom captured

## Phase 3 — Hypothesise

**3-5 ranked hypotheses** before testing any. Each falsifiable:

> "If X is cause, then changing Y makes bug disappear / changing Z makes it worse."

Show list to user — they often re-rank or rule out instantly.

**Cap**: after 2 falsified hypotheses, stop — re-enter Phase 1 (loop too slow) or ask the user (access gap).

## Phase 4 — Instrument

One variable at a time. Map probe to prediction.

| Prefer | Tool                                      |
| ------ | ----------------------------------------- |
| 1      | Debugger/REPL (one breakpoint > ten logs) |
| 2      | Targeted logs at hypothesis boundaries    |
| Never  | "log everything and grep"                 |

**Tag debug logs**: `[DEBUG-a4f2]` → cleanup = single grep. **Perf bugs**: Measure first, then bisect.

**Multi-component systems (CI→build→sign, API→service→DB):** instrument every boundary first —
log data in/out + config propagation per layer, run once, identify failing layer from evidence.
Don't investigate component-by-component.

**User signals to heed:** "Is that not happening?" (assumed, not verified) · "Stop guessing" ·
"We're stuck?" (approach wrong) → return to Phase 1.

**Unknown which test pollutes state** → `scripts/find-polluter.sh <path> <test_glob> [test_cmd]` (auto-detects npm/pytest).

## Phase 5 — Fix + Regression Test

Write test **before** fix — follow [[test-driven-development]] (watch it fail first).

1. Repro → failing test → watch fail → fix → watch pass → re-run Phase 1 loop

**Seam selection**: `query_temporal.py callers <name>` — cover the most real callers. Input-space bugs (not logic) →
property test over example test ([[python/property-testing]]).

**3 failed fixes, each revealing new problems elsewhere → stop.** Wrong architecture, not wrong hypothesis: each fix
needs "massive refactoring", new symptoms appear per fix. Question the pattern with the user before fix #4.

## Phase 6 — Cleanup

- [ ] Original repro no longer reproduces
- [ ] `rg '\[DEBUG-' src/` returns empty
- [ ] Correct hypothesis in commit message

## Language Tables

| Language | Reference |
| --- | --- |
| Python | [references/python.md](references/python.md) |

## Techniques

| Reference | Contents |
| --- | --- |
| [references/root-cause-tracing.md](references/root-cause-tracing.md) | Trace bugs backward through the call stack to the original trigger |
| [references/defense-in-depth.md](references/defense-in-depth.md) | Validate at every layer; make the bug structurally impossible |
| [references/condition-based-waiting.md](references/condition-based-waiting.md) | Replace arbitrary timeouts with condition polling |
