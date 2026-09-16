---
name: python/testing
description: Pytest core - assertions, markers, commands, config
invocation: auto
---

# Pytest Core

## Targeted Testing

**NEVER `pytest tests/`** — scope to changed modules:

```bash
pytest tests/foo/test_bar.py -x           # specific file
pytest tests/foo/test_bar.py::test_func   # specific test
pytest -k "login and not slow"            # keyword match
```

Mirror: `src/foo/bar.py` → `tests/foo/test_bar.py`

## Basic Patterns

```python
def test_addition():
    assert 2 + 3 == 5

def test_exception():
    with pytest.raises(ValueError, match="invalid"):
        int("not_a_number")

class TestCalculator:
    def test_add(self):
        assert Calculator().add(2, 3) == 5
```

## Assertions

```python
assert x == y
assert x != y
assert x in collection
assert isinstance(obj, MyClass)
assert 0.1 + 0.2 == pytest.approx(0.3)

with pytest.raises(ValueError) as exc_info:
    raise ValueError("bad")
assert "bad" in str(exc_info.value)
```

## Parametrize

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", 5), ("", 0), ("pytest", 6),
], ids=["normal", "empty", "keyword"])
def test_string_length(input, expected):
    assert len(input) == expected
```

## Markers

```python
@pytest.mark.slow
def test_large_dataset(): ...

@pytest.mark.skip(reason="Not implemented")
def test_future_feature(): ...

@pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
def test_unix_permissions(): ...

@pytest.mark.xfail(reason="Known bug #123")
def test_known_bug(): ...

@pytest.mark.asyncio
async def test_async_func(): ...
```

## Commands

| Flag          | Purpose                 |
| ------------- | ----------------------- |
| `-x`          | Stop on first failure   |
| `--lf`        | Rerun last failed       |
| `-k "expr"`   | Match by keyword        |
| `-m "marker"` | Match by marker         |
| `-v`          | Verbose output          |
| `--tb=short`  | Short traceback         |
| `-n auto`     | Parallel (pytest-xdist) |
| `--cov=src`   | Coverage (pytest-cov)   |

## pyproject.toml Config

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "slow: marks test as slow",
    "integration: integration tests",
]
addopts = "-v --tb=short"
filterwarnings = ["ignore::DeprecationWarning"]
```

## Anti-Patterns

| Bad                   | Good                   | Why                        |
| --------------------- | ---------------------- | -------------------------- |
| `self.assertEqual()`  | `assert x == y`        | pytest rewrites for output |
| Setup in `__init__`   | `@pytest.fixture`      | Lifecycle management       |
| Global state          | Fixture with `yield`   | Proper cleanup             |
| Huge test functions   | Small focused tests    | Easier debugging           |
| `tests/` (full suite) | `tests/path/test_X.py` | Token/time efficiency      |

## Debug

```python
breakpoint()                           # drop into debugger
pytest --pdb                           # enter pdb on failure
pytest -s                              # show print output
```

[[python/conftest]] [[python/mocking]] [[python/property-testing]] [[python/test-gen]]
