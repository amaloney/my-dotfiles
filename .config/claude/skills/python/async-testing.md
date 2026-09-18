---
name: python/async-testing
description: Async testing with pytest-asyncio - fixtures, clients, concurrent tests
invocation: auto
---

# Async Testing (pytest-asyncio)

## Setup

```bash
uv add --group test pytest-asyncio
```

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"  # or use @pytest.mark.asyncio per test
```

## Basic Patterns

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_function():
    result = await fetch_data()
    assert result["status"] == "ok"

@pytest.mark.asyncio
async def test_concurrent_requests():
    results = await asyncio.gather(
        fetch("/api/users"),
        fetch("/api/products"),
        fetch("/api/orders"),
    )
    assert all(r.status == 200 for r in results)
```

## Async Fixtures

```python
@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture(scope="session")
async def db_pool():
    pool = await asyncpg.create_pool("postgresql://localhost/test")
    yield pool
    await pool.close()

@pytest.mark.asyncio
async def test_create_user(async_client):
    response = await async_client.post("/users", json={"name": "Alice"})
    assert response.status_code == 201
```

## Async Mocking

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_async_service():
    with patch("myapp.client.fetch", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": "test"}
        result = await process_data()
        assert result == "test"
        mock.assert_awaited_once()

@pytest.mark.asyncio
async def test_multiple_awaits(mocker):
    mock_fetch = mocker.patch("myapp.api.fetch", new_callable=AsyncMock)
    mock_fetch.side_effect = [{"id": 1}, {"id": 2}]
    
    r1 = await fetch_user(1)
    r2 = await fetch_user(2)
    
    assert mock_fetch.await_count == 2
```

## Timeout & Cancellation

```python
@pytest.mark.asyncio
@pytest.mark.timeout(5)  # pytest-timeout
async def test_with_timeout():
    await long_running_operation()

@pytest.mark.asyncio
async def test_cancellation():
    task = asyncio.create_task(slow_operation())
    await asyncio.sleep(0.1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
```

## Anti-Patterns

| Bad | Good |
|-----|------|
| `asyncio.run()` in test | `@pytest.mark.asyncio` decorator |
| `time.sleep()` | `await asyncio.sleep()` |
| Sync fixture for async resource | Async fixture with `yield` |
| Missing `await` on mock | `mock.assert_awaited_once()` |

[[python/testing]] [[python/mocking]] [[python/conftest]]
