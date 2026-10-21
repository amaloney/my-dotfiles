# code-hygiene pattern memory

```python
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
```

```python
# BAD — "fixing" a typo in a ported error message (parity/golden tests pin message text; this changes behavior)
msg = "To be implemnted by the inheriting class."
raise NotImplementedError(msg)

# GOOD — leave ported strings byte-identical; hygiene renames identifiers, never literals
msg = "To be implemnted by the inheriting class."  # sic — ported contract
raise NotImplementedError(msg)
```

```python
# BAD — exact placeholder match silently no-ops once the template gets formatted
html = template.read_text().replace("/*__GRAPH_DATA__*/null", payload)

# GOOD — whitespace-tolerant match, exactly-one assertion, callable sub so backslashes
# in the JSON payload stay literal instead of being read as regex escapes
placeholder = re.compile(r"/\*__GRAPH_DATA__\*/\s*null")
count = len(placeholder.findall(template_text))
if count != 1:
    raise SystemExit(f"expected exactly one graph placeholder in {template_path}, found {count}")
html = placeholder.sub(lambda _: payload, template_text)
```

