# Good Tests

A test exists to catch a specific break. Two principles:

1. Every test names the break it catches
2. Every test exercises the real thing

## Gate 1: Name the Break

Before writing the test body: **what production change should make this test fail — bug or decision?**

| Answer | Action |
| --- | --- |
| Can't name one | Redesign around an observable behavior |
| Only intentional decisions fail it | Change detector — test the behavior that depends on the decision |
| "The source text changed" | Never grep source; run the artifact, assert its effects |

**Mirror assertion ban** — expectation computed by the code under test passes no matter what:

```typescript
// Bad: same builder computes both sides — always true
const expected = buildSearchQuery({ tag: "urgent" });
expect(buildSearchQuery({ tag: "urgent" })).toBe(expected);

// Good: hand-derived literal
expect(buildSearchQuery({ tag: "urgent" })).toBe('tag:"urgent"');
```

**Your boundary, not the framework's** — test the contract your code makes (route registered, query emitted,
payload produced). Framework mechanics are the maintainers' tests. Trivial constructors/getters/constants earn
tests only when they validate, normalize, or cause side effects.

## Gate 2: Exercise the Real Thing

Mock-level details: [[python/mocking]]. Unique rules here:

- **Mocks earn no assertions** — asserting on the mock says nothing about the component; unmock or delete
- **Mirror real data completely** — all documented fields, not just the ones read; partial mocks pass while
  integration breaks
- **No test-only methods on production classes** — cleanup only tests need lives in test utilities
- **Mock setup > half the test → integration test with real components**

## Mutation Check

Before finishing: mentally mutate the production code; at least one test should fail per realistic mutation:

- Wrong constant or argument
- Wrong branch handler
- Missing state change or side effect
- Empty/default return
- Missing validation for zero, empty, nil, unauthorized, malformed

A mutation nothing catches = unprotected behavior or tautological test.

## Warning Signs

- Setup and assertion share the same object (guaranteed equality)
- Test fails only on intentional changes, never on accidental breakage
- Expected values hidden behind loops/builders/helpers
- Test greps source text
- Assertion checks a `*-mock` test ID
- Method called only from test files
- Mocking "just to be safe"
