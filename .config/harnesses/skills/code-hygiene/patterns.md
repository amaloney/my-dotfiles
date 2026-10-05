# code-hygiene pattern memory

# BAD — generator fixture annotated with the yielded type (ANN stays green; annotation is wrong)
@pytest.fixture
def mock_get() -> MagicMock:
    with patch("mod.requests.get") as mock:
        yield mock

# GOOD — annotate the iterator; matches how pytest types generator fixtures
@pytest.fixture
def mock_get() -> Iterator[MagicMock]:
    with patch("mod.requests.get") as mock:
        yield mock
