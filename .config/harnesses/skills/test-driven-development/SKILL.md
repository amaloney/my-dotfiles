---
name: test-driven-development
description: Write failing test before production code - red-green-refactor
invocation: auto
adapted-from: obra/superpowers v6.4.2 (MIT)
---

# Test-Driven Development

Write the test first. Watch it fail. Write minimal code to pass. If you didn't watch the test fail,
you don't know it tests the right thing.

## Iron Law

No production code without a failing test first. Code written before the test → delete it, start over.
No "keep as reference", no "adapt it while writing tests". Delete means delete.

Exceptions (ask the user first): throwaway prototypes, generated code, config files.

## Red-Green-Refactor

1. **RED** — one minimal test: one behavior, clear name, real code (mocks only if unavoidable)
2. **Verify RED** — run it. Must fail (not error), for the expected reason (feature missing, not typo).
   Passes immediately → you're testing existing behavior; fix the test.
3. **GREEN** — simplest code that passes. No extra features, no "while I'm here" improvements.
4. **Verify GREEN** — run the **full suite**, not just your file. A red test you scrolled past and didn't
   report is a report falsified by omission. Other tests fail → fix now.
5. **REFACTOR** — only while green: remove duplication, improve names, extract helpers. No new behavior.
6. Repeat.

```typescript
// RED: test('retries failed operations 3 times', ...) — expect(result).toBe('success'); expect(attempts).toBe(3)
// GREEN: for (let i = 0; i < 3; i++) { try { return await fn(); } catch (e) { if (i === 2) throw e; } }
```

Good tests: [references/good-tests.md](references/good-tests.md) — name the break it catches; exercise the real thing.

## Rationalizations

| Excuse | Reality |
| --- | --- |
| "Too simple to test" | Simple code breaks. Test takes 30 seconds |
| "I'll test after" | Tests-after prove nothing — you never watched it fail |
| "Manually tested already" | No record, no re-run, easy to forget cases |
| "Deleting X hours is wasteful" | Sunk cost. Keeping untrusted code is the waste |
| "TDD is dogmatic" | Catches bugs before commit; enables fearless refactor |
| "Explore first" | Fine — throw away exploration, then start with TDD |

## When Stuck

| Problem | Solution |
| --- | --- |
| Don't know how to test | Write the wished-for API; write the assertion first |
| Test too complicated | Design too complicated — simplify the interface |
| Must mock everything | Code too coupled — dependency injection |
| Test setup huge | Extract helpers; still complex → simplify design |

## Debugging Integration

Bug found → write failing test reproducing it → TDD cycle. Test proves the fix and prevents regression.
Never fix bugs without a test. Full diagnosis: [[debugging]] Phase 5.

## Verification Checklist

- [ ] Every new function/method has a test
- [ ] Watched each test fail before implementing
- [ ] Each failed for the expected reason
- [ ] Minimal code to pass each test
- [ ] Full suite passes, output pristine
- [ ] Real code over mocks (mocks only if unavoidable)
- [ ] Edge cases and errors covered
