"""Tests for PyPI metadata fetching."""

from pathlib import Path
from unittest.mock import MagicMock, patch


def _mock_response(payload: dict, ok: bool = True) -> MagicMock:
    response = MagicMock()
    response.ok = ok
    response.json.return_value = payload
    return response


def test_fetch_returns_dict_on_success() -> None:
    from metadata_observer.pypi import fetch_pypi_metadata

    with patch("metadata_observer.pypi.requests.get", return_value=_mock_response({"info": {"name": "requests"}})):
        result = fetch_pypi_metadata("requests")

    assert result == {"info": {"name": "requests"}}


def test_fetch_returns_none_on_404() -> None:
    from metadata_observer.pypi import fetch_pypi_metadata

    with patch("metadata_observer.pypi.requests.get", return_value=_mock_response({}, ok=False)):
        result = fetch_pypi_metadata("nonexistent-pkg-xyz")

    assert result is None


def test_fetch_caches_on_success(tmp_path: Path) -> None:
    from metadata_observer.pypi import fetch_pypi_metadata

    with patch("metadata_observer.pypi.requests.get", return_value=_mock_response({"info": {}})):
        fetch_pypi_metadata("requests", cache_dir=tmp_path)

    cache_file = tmp_path / "pypi.json"
    assert cache_file.exists()
    import json

    assert json.loads(cache_file.read_text()) == {"info": {}}


def test_fetch_no_cache_when_none(tmp_path: Path) -> None:
    from metadata_observer.pypi import fetch_pypi_metadata

    with patch("metadata_observer.pypi.requests.get", return_value=_mock_response({"info": {}})):
        fetch_pypi_metadata("requests")

    assert not (tmp_path / "pypi.json").exists()


def test_normalizes_pep503_name() -> None:
    from metadata_observer.pypi import fetch_pypi_metadata

    with patch("metadata_observer.pypi.requests.get", return_value=_mock_response({})) as mock_get:
        fetch_pypi_metadata("Foo_Bar")

    url = mock_get.call_args[0][0]
    assert "foo-bar" in url
