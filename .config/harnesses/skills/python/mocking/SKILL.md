---
name: python/mocking
description: Mock patterns - patch, MagicMock, pytest-mock, monkeypatch
invocation: auto
---

# Mocking Patterns

## pytest-mock (Preferred)

```python
def test_api_call(mocker):
    mock_get = mocker.patch("myapp.service.requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"users": []}

    result = get_users()

    mock_get.assert_called_once_with("https://api.example.com/users")
    assert result == []
```

## unittest.mock

```python
from unittest.mock import patch, MagicMock, Mock, PropertyMock

@patch("myapp.service.database")
def test_save(mock_db):
    mock_db.save.return_value = True
    assert save_user({"name": "Alice"})
    mock_db.save.assert_called_once()

# Context manager
def test_with_context():
    with patch("myapp.client.requests") as mock_req:
        mock_req.get.return_value.ok = True
        assert fetch_data()
```

## Patch Targets

Patch where used, not where defined:

```python
# myapp/service.py
from myapp.client import api_client  # imported here

# tests/test_service.py
@patch("myapp.service.api_client")  # patch in service, not client
def test_service(mock_client):
    ...
```

## MagicMock vs Mock

| Type        | Has                                   |
| ----------- | ------------------------------------- |
| `Mock`      | Basic mock, configure manually        |
| `MagicMock` | Magic methods (`__len__`, `__iter__`) |

```python
mock = MagicMock()
mock.__len__.return_value = 5
assert len(mock) == 5

mock.__iter__.return_value = iter([1, 2, 3])
assert list(mock) == [1, 2, 3]
```

## Return Values & Side Effects

```python
mock.return_value = "fixed"
mock.side_effect = ValueError("boom")  # raises
mock.side_effect = [1, 2, 3]           # sequential returns
mock.side_effect = lambda x: x * 2     # computed
```

## Assertions

```python
mock.assert_called()
mock.assert_called_once()
mock.assert_called_with(arg1, key=val)
mock.assert_called_once_with(arg1)
mock.assert_not_called()
mock.assert_any_call(arg1)  # any call matched

# Call inspection
mock.call_count
mock.call_args       # last call
mock.call_args_list  # all calls
```

## Monkeypatch (pytest)

```python
def test_env_var(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    assert os.environ["API_KEY"] == "test-key"

def test_chdir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert Path.cwd() == tmp_path

def test_setattr(monkeypatch):
    monkeypatch.setattr("myapp.config.DEBUG", True)
    assert config.DEBUG is True
```

## Spy (watch without replacing)

```python
def test_spy(mocker):
    spy = mocker.spy(myapp.service, "process")
    result = myapp.service.process(data)  # real call
    spy.assert_called_once_with(data)
```

## Async Mocking

```python
@pytest.mark.asyncio
async def test_async(mocker):
    mock_fetch = mocker.patch("myapp.api.fetch")
    mock_fetch.return_value = asyncio.coroutine(lambda: {"data": 1})()
    # or
    mock_fetch.return_value = {"data": 1}  # if awaited directly

    result = await myapp.api.fetch()
    assert result == {"data": 1}
```

## Anti-Patterns

| Bad                          | Good                             |
| ---------------------------- | -------------------------------- |
| Mock everything              | Mock only boundaries             |
| Patch where defined          | Patch where used                 |
| No assertions on mock        | Verify mock was called correctly |
| Mock internal implementation | Mock external dependencies       |

[[python/testing]] [[python/conftest]] [[python/bugs]]
