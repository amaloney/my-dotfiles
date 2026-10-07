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

# BAD — "fixing" a typo in a ported error message (parity/golden tests pin message text; this changes behavior)
msg = "To be implemnted by the inheriting class."
raise NotImplementedError(msg)
# GOOD — leave ported strings byte-identical; hygiene renames identifiers, never literals
msg = "To be implemnted by the inheriting class."  # sic — ported contract
raise NotImplementedError(msg)
