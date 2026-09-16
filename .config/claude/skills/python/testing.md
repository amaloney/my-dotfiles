---
name: python/testing
description: Pytest patterns and fixtures
invocation: auto
---

# Pytest

## Targeted Testing

**NEVER `tests/` or `tests/unit/`** — full suite burns tokens + time. Scope to changed modules:

```bash
# Changed src/foo/bar.py → run only its tests
pytest tests/foo/test_bar.py -x

# Multiple changes → multiple specific paths
pytest tests/foo/test_bar.py tests/baz/test_qux.py -x

# Unknown test location → find first
fd "test_bar" tests/
```

| ❌ Banned            | ✅ Instead                            |
| -------------------- | ------------------------------------- |
| `pytest tests/`      | `pytest tests/mod/test_X.py`          |
| `pytest tests/unit/` | `pytest tests/unit/test_X.py`         |
| `pixi run test`      | `pixi run pytest tests/.../test_X.py` |

Mirror: `src/foo/bar.py` → `tests/foo/test_bar.py` or `tests/unit/test_bar.py`

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
