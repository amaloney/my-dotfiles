---
name: python/testing
description: Pytest patterns and fixtures
invocation: auto
---

# Pytest

## Targeted Testing

**Never run full suite** — test only changes:

`pytest tests/test_<mod>.py` | `pytest -k "pattern"` | `pytest --lf`

Mirror structure: `src/foo/bar.py` → `tests/foo/test_bar.py`

## Hypothesis (prefer)

```python
@given(st.integers())
def test_prop(n):
    assert func(n) == expected
```

`st.integers()` | `st.text()` | `st.lists(st.X())` | `st.dictionaries()`

## Fixtures

```python
@pytest.fixture(scope="module")
def resource():
    conn = connect()
    yield conn
    conn.close()
```

## Patterns

```python
def test_raises():
    with pytest.raises(ValueError, match="msg"):
        func(bad)

@patch("mod.api")
def test_mock(mock_api):
    mock_api.return_value = "x"
```

## Markers

`@pytest.mark.slow` | `@pytest.mark.skip` | `@pytest.mark.asyncio`

## Commands

`-x` stop first | `--lf` rerun failed | `-k` match | `--cov=src/mod` scoped coverage

**Full suite**: CI only.

[[python/bugs]] [[python/style]]
