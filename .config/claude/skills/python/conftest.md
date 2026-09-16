---
name: python/conftest
description: Pytest shared fixtures - conftest.py patterns, scoping, factories
invocation: auto
---

# Conftest Patterns

## Scope Hierarchy

```
conftest.py          # root - available everywhere
tests/conftest.py    # test root
tests/unit/conftest.py      # unit only
tests/integration/conftest.py  # integration only
```

Fixtures in parent conftest available to children. No imports needed.

## Fixture Scopes

| Scope      | Lifecycle           | Use Case                |
| ---------- | ------------------- | ----------------------- |
| `function` | Each test (default) | Isolated state          |
| `class`    | Each test class     | Shared class setup      |
| `module`   | Each test file      | Expensive per-file init |
| `package`  | Each test directory | Shared package resource |
| `session`  | Entire test run     | DB connection, server   |

```python
@pytest.fixture(scope="session")
def db_connection():
    conn = Database.connect()
    yield conn
    conn.close()

@pytest.fixture(scope="function")
def db_transaction(db_connection):
    tx = db_connection.begin()
    yield tx
    tx.rollback()
```

## Factory Fixtures

```python
@pytest.fixture
def make_user():
    created = []
    def _make(name="test", email=None):
        user = User(name=name, email=email or f"{name}@test.com")
        created.append(user)
        return user
    yield _make
    for u in created:
        u.delete()

def test_multiple_users(make_user):
    alice = make_user("alice")
    bob = make_user("bob")
    assert alice.id != bob.id
```

## Autouse

```python
@pytest.fixture(autouse=True)
def reset_state():
    State.reset()
    yield
    State.cleanup()

@pytest.fixture(autouse=True, scope="session")
def setup_logging():
    logging.basicConfig(level=logging.DEBUG)
```

## Parametrized Fixtures

```python
@pytest.fixture(params=["sqlite", "postgres"])
def db(request):
    if request.param == "sqlite":
        return SQLiteDB()
    return PostgresDB()

def test_query(db):  # runs twice, once per param
    assert db.query("SELECT 1")
```

## Request Object

```python
@pytest.fixture
def resource(request):
    name = request.node.name  # test name
    markers = request.node.iter_markers()  # test markers

    if request.node.get_closest_marker("slow"):
        return HeavyResource()
    return LightResource()
```

## Temp Paths

```python
@pytest.fixture
def config_file(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("debug: true")
    return cfg

@pytest.fixture(scope="session")
def shared_cache(tmp_path_factory):
    return tmp_path_factory.mktemp("cache")
```

## Common conftest.py

```python
# tests/conftest.py
import pytest
from myapp import create_app, db

@pytest.fixture(scope="session")
def app():
    app = create_app(testing=True)
    yield app

@pytest.fixture(scope="function")
def client(app):
    return app.test_client()

@pytest.fixture(scope="function")
def db_session(app):
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.rollback()
        db.drop_all()
```

[[python/testing]] [[python/mocking]] [[python/property-testing]]
