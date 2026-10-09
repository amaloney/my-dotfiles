---
name: rust/property-testing
description: proptest property-based testing - strategies, shapes, shrinking, regression files
invocation: auto
---

# Property-Based Testing (proptest)

Handoff: `next: done`.

## When to Use

Recognize algebraic shapes (same catalogue as Python — the method is language-agnostic):

| Property       | Formula                  | Where it applies                     |
| -------------- | ------------------------ | ------------------------------------ |
| Roundtrip      | `decode(encode(x)) == x` | serde, parsers/printers, `FromStr`/`Display` |
| Inverse        | `f(g(x)) == x`           | encrypt/decrypt, compress/decompress |
| Oracle         | `new(x) == reference(x)` | optimization, rewrite, unsafe fast path vs safe one |
| Idempotence    | `f(f(x)) == f(x)`        | normalization, formatting, dedup     |
| Invariant      | Holds before and after   | collections, state machines          |
| Easy to verify | `is_sorted(sort(x))`     | complex algo with cheap checker      |
| Commutativity  | `f(a, b) == f(b, a)`     | merges, set ops                      |

**Strength ordering** (weakest → strongest): `no panic → invariant → idempotence → roundtrip/oracle`.
Assert the strongest property the code supports. "No panic" alone is fuzzing — use `cargo fuzz` for that instead.

## Core patterns

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn display_parse_roundtrip(version in any::<Version>()) {
        let text = version.to_string();
        prop_assert_eq!(text.parse::<Version>().unwrap(), version);
    }

    #[test]
    fn normalize_is_idempotent(input in "\\PC{0,64}") {          // regex strategy: any printable, ≤64 chars
        let once = normalize(&input);
        prop_assert_eq!(normalize(&once), once);
    }
}
```

Use `prop_assert!`/`prop_assert_eq!` inside `proptest!` — plain `assert!` panics and shrinks worse.

## Strategies

| Need                       | Strategy                                                |
| -------------------------- | ------------------------------------------------------- |
| Any value of a type        | `any::<T>()` — derive with `#[derive(proptest_derive::Arbitrary)]` |
| Bounded numbers            | `0u32..1000`                                            |
| Strings by shape           | regex literal `"[a-z]{1,16}"`                           |
| Collections                | `prop::collection::vec(elem, 0..50)`                    |
| One of                     | `prop_oneof![Just(Mode::A), Just(Mode::B)]`             |
| Composite domain values    | `prop_compose! { fn arb_user()(id in 1u64.., name in "[a-z]{3,12}") -> User { User { id, name } } }` |
| Derived constraint         | `.prop_map(...)` / `.prop_filter("reason", ...)` (filter sparingly — rejections slow the run) |

Generate valid inputs by construction rather than filtering invalid ones.

## Shrinking and regressions

Failures shrink to a minimal case and are recorded in `proptest-regressions/<module>.txt`. **Commit these files** —
they are replayed first on every run, turning a found bug into a permanent regression test. Also add an explicit
`#[test]` for the minimized case when fixing it ([[rust/testing]]).

## Anti-patterns

- **Property restates the implementation** (`prop_assert_eq!(add(a, b), a + b)`) — asserts nothing; use an oracle that
  is independent.
- **Tautology after filtering** — a `prop_filter` that leaves only trivially passing inputs.
- **Unbounded sizes** — `vec(any::<T>(), 0..)` blows up runtime; bound every collection.
- **Overflow in the property itself** — use `wrapping_*`/`checked_*` in the oracle, or bound the ranges.

[[rust/testing]]
