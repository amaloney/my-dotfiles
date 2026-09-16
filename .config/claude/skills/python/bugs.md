---
name: python/bugs
description: Diagnosis methodology + Python bug patterns
invocation: auto
---

# Diagnose

## Methodology

Skip phases only when explicitly justified.

### Phase 1 — Build Feedback Loop

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

**Non-deterministic**: Loop 100×, parallelise, add stress. Raise repro rate until debuggable.

**Cannot build loop?** Stop. List what tried. Ask user for: env access, captured artifact, or prod instrumentation
permission.

### Phase 2 — Reproduce

- [ ] Failure matches **user's** description (not nearby different bug)
- [ ] Reproducible across runs (or high enough rate)
- [ ] Exact symptom captured

### Phase 3 — Hypothesise

**3-5 ranked hypotheses** before testing any. Each falsifiable:

> "If X is cause, then changing Y makes bug disappear / changing Z makes it worse."

Show list to user — they often re-rank or rule out instantly.

### Phase 4 — Instrument

One variable at a time. Map probe to prediction.

| Prefer | Tool                                      |
| ------ | ----------------------------------------- |
| 1      | Debugger/REPL (one breakpoint > ten logs) |
| 2      | Targeted logs at hypothesis boundaries    |
| Never  | "log everything and grep"                 |

**Tag debug logs**: `[DEBUG-a4f2]` → cleanup = single grep. **Perf bugs**: Measure first, then bisect.

### Phase 5 — Fix + Regression Test

Write test **before** fix — but only at correct seam (exercises real bug pattern).

1. Repro → failing test → watch fail → fix → watch pass → re-run Phase 1 loop

### Phase 6 — Cleanup

- [ ] Original repro no longer reproduces
- [ ] All `[DEBUG-...]` removed
- [ ] Correct hypothesis in commit message

---

## Python

### Common Bugs {#common-bugs}

| Pattern                          | Bug                             | Fix                        |
| -------------------------------- | ------------------------------- | -------------------------- |
| Mutable default                  | `def f(x=[]):`                  | `x=None`; `x = x or []`    |
| Late binding                     | `[lambda: i for i in range(3)]` | `lambda i=i: i`            |
| Shadow builtin {#shadow-builtin} | `list = []`                     | Rename                     |
| Identity                         | `x is []`                       | `x == []`                  |
| Reference                        | `b = a` mutates both            | `b = a.copy()`             |
| Bare except {#bare-except}       | Catches `KeyboardInterrupt`     | `except Exception as exc:` |
| None access                      | `obj.method().attr`             | Guard with walrus/if       |

### Infinite Loops

| Pattern                               | Fix                                  |
| ------------------------------------- | ------------------------------------ |
| Status polling (only expected states) | Handle ALL terminal states + timeout |
| Queue without visited                 | Track visited set                    |
| Condition never met                   | Add timeout/max iterations           |

### TUI/GUI Memory Leaks

| Pattern                  | Fix                           |
| ------------------------ | ----------------------------- |
| Unbounded widget mount   | Cap count, remove oldest      |
| Event log accumulation   | Track count, remove when full |
| Markup with user content | `markup=False` for untrusted  |

### Async

Missing `await` → add it | Blocking in async → `run_in_executor`

### Imports

Circular → move inside function | Stale `.pyc` → `find . -name "*.pyc" -delete`

### Detection

```bash
rg -n "\._[a-z][a-z_]+\(" --type py | grep -v "self\._\|cls\._"  # Underscore typos
rg -n "except:" --type py                                        # Bare excepts
ruff check --select F401,F821 src/                               # Unused/undefined
```

**Debug**: `breakpoint()` | `from rich import inspect; inspect(obj)`

[[python/style]] [[python/testing]] [[python/property-testing]] [[python/types]] [[python/errors]]
