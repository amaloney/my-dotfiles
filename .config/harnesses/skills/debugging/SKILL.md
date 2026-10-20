---
name: debugging
description: Bug diagnosis methodology - feedback loop, reproduce, hypothesise, instrument, fix, cleanup
invocation: auto
adapted-from: obra/superpowers v6.4.2 (MIT)
---

# Debugging

Handoff: `next: test-driven-development`.

Skip phases only when explicitly justified.

## Iron Law

No fixes without root-cause investigation. Symptom fixes = failure.

| Excuse                 | Reality                  |
| ---------------------- | ------------------------ |
| "Simple, skip process" | Simple bugs have causes  |
| "Emergency"            | Systematic > thrashing   |
| "Multiple fixes"       | Can't isolate            |
| "One more" (2+ failed) | 3 = architecture problem |

## Phase 0 — Triage

Static checks: Python `ast_checker.py --check bugs src/` + `query_temporal.py impact <fn>`; Rust
`cargo clippy -- -W clippy::correctness -W clippy::suspicious`. Language patterns: [references/python.md],
[references/rust.md], [[bug]].

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

**Iterate**: 2s deterministic > 30s flaky. Non-deterministic → loop 100×, stress. Snapshot to
`.scratch/debug-<task>/env.txt`. Cannot build loop → stop, list attempts, ask user.

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

One variable at a time. Debugger > targeted logs > never "log everything". Tag logs `[DEBUG-xxxx]` for cleanup.
Multi-component: instrument all boundaries first, identify failing layer. Perf: measure then bisect. User says "stop
guessing" / "stuck" → Phase 1. Test pollution → `scripts/find-polluter.sh`.

## Phase 5 — Fix + Regression Test

[[test-driven-development]]: test first → watch fail → fix → pass → re-run loop. Seam: `query_temporal.py callers` —
cover real callers. Input-space → property test. 3 failed fixes each revealing new problems → stop (wrong architecture).

## Phase 6 — Cleanup

- [ ] Original repro no longer reproduces
- [ ] `rg '\[DEBUG-' src/` returns empty
- [ ] Correct hypothesis in commit message

## Language Tables

| Language | Reference                                    |
| -------- | -------------------------------------------- |
| Python   | [references/python.md](references/python.md) |
| Rust     | [references/rust.md](references/rust.md)     |

## Techniques

| Reference                                                                      | Contents                                                           |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| [references/root-cause-tracing.md](references/root-cause-tracing.md)           | Trace bugs backward through the call stack to the original trigger |
| [references/defense-in-depth.md](references/defense-in-depth.md)               | Validate at every layer; make the bug structurally impossible      |
| [references/condition-based-waiting.md](references/condition-based-waiting.md) | Replace arbitrary timeouts with condition polling                  |
