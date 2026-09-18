---
name: python/property-testing
description: Hypothesis property-based testing - strategies, shapes, shrinking
invocation: auto
---

# Property-Based Testing (Hypothesis)

## When to Use

Recognize algebraic shapes:

| Property | Formula | Where it applies |
|----------|---------|------------------|
| Roundtrip | `decode(encode(x)) == x` | Serialization, conversion pairs |
| Inverse | `f(g(x)) == x` | encrypt/decrypt, compress/decompress |
| Oracle | `new(x) == reference(x)` | Optimization, refactor, reimplement |
| Idempotence | `f(f(x)) == f(x)` | Normalization, formatting, sorting |
| Invariant | Holds before and after | Any transformation, state machine |
| Easy to verify | `is_sorted(sort(x))` | Complex algo with cheap checker |
| Commutativity | `f(a, b) == f(b, a)` | Binary and set operations |
| Identity | `f(x, e) == x` | Operations with neutral element |

**Strength ordering** (weakest → strongest):
`no crash → type preservation → invariant → idempotence → roundtrip/oracle`

Assert the strongest property the code supports. "No crash" alone rarely justifies the dependency.

## Core Patterns

```python
from hypothesis import given, strategies as st, settings, assume

@given(st.text())
def test_roundtrip(s):
    assert decode(encode(s)) == s

@given(st.integers(), st.integers())
def test_add_commutative(a, b):
    assert add(a, b) == add(b, a)

@given(st.lists(st.integers()))
def test_sort_idempotent(xs):
    assert sorted(sorted(xs)) == sorted(xs)
```

## Strategies

| Strategy                       | Generates                   |
| ------------------------------ | --------------------------- |
| `st.integers()`                | ints (unbounded)            |
| `st.integers(min_value=0)`     | non-negative ints           |
| `st.floats(allow_nan=False)`   | floats without NaN          |
| `st.text()`                    | unicode strings             |
| `st.text(alphabet="abc")`      | strings from alphabet       |
| `st.binary()`                  | bytes                       |
| `st.booleans()`                | True/False                  |
| `st.none()`                    | None                        |
| `st.lists(st.X())`             | lists of X                  |
| `st.lists(st.X(), min_size=1)` | non-empty lists             |
| `st.dictionaries(st.X, st.Y)`  | dicts                       |
| `st.tuples(st.X(), st.Y())`    | fixed-length tuples         |
| `st.one_of(st.X(), st.Y())`    | union                       |
| `st.sampled_from([a, b, c])`   | pick from list              |
| `st.builds(MyClass, st.X())`   | construct objects           |
| `st.from_type(MyType)`         | infer from type annotations |

## Composite Strategies

```python
@st.composite
def valid_user(draw):
    name = draw(st.text(min_size=1, max_size=50))
    age = draw(st.integers(min_value=0, max_value=150))
    return User(name=name, age=age)

@given(valid_user())
def test_user_creation(user):
    assert user.is_valid()
```

## Filtering & Assumptions

```python
@given(st.integers())
def test_positive_only(n):
    assume(n > 0)  # skip if false
    assert sqrt(n) >= 0

# Or filter in strategy
@given(st.integers().filter(lambda n: n > 0))
def test_positive(n):
    assert sqrt(n) >= 0
```

## Settings

```python
@settings(max_examples=1000, deadline=None)
@given(st.text())
def test_slow_property(s):
    ...

# In conftest.py
from hypothesis import settings
settings.register_profile("ci", max_examples=1000)
settings.register_profile("dev", max_examples=100)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))
```

## Counterexample Triage

When test fails with shrunk example:

1. **Wrong property?** Does the property actually hold? Check edge cases
2. **Ambiguous spec?** Is behavior undefined for this input?
3. **Real bug?** Code violates the intended property → fix code

```python
# Hypothesis prints minimal failing example
Falsifying example: test_roundtrip(s='\x00')
# Investigate: is null byte valid input? Should encode handle it?
```

## Two Ways a Property Asserts Nothing

| Trap | Example | Fix |
|------|---------|-----|
| **Tautology** | `assert add(a, b) == a + b` | Restates implementation — pick property that constrains without recomputing |
| **Vacuity** | Heavy `assume()` filtering | Filters out nearly every input — push constraints into strategy instead |

Exception: `f(x) == f(x)` is valid determinism property when `f` is not obviously pure (serializers, hashing, clock readers).

## Anti-Patterns

| Bad                          | Good                              |
| ---------------------------- | --------------------------------- |
| `assert True`                | Assert actual property            |
| Test only happy path         | Include edge cases in strategy    |
| Ignore shrunk example        | Investigate root cause            |
| `@given(st.integers(0, 10))` | Use full range unless constrained |
| `assume(complex_predicate)`  | Build constraint into strategy    |
| Restate implementation       | Find algebraic property           |

[[python/testing]] [[python/conftest]] [[python/bugs]]
