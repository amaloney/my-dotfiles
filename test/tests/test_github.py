"""Tests for GitHub metadata fetching."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _mock_urlopen(payload: bytes, headers: dict | None = None) -> MagicMock:
    response = MagicMock()
    response.read.return_value = payload
    response.headers = headers or {}
    response.__enter__ = lambda s: s
    response.__exit__ = MagicMock(return_value=False)
    return response


def test_fetch_returns_dict_on_success() -> None:
    from metadata_observer.github import fetch_github_metadata

    with patch("metadata_observer.github.urlopen", return_value=_mock_urlopen(b'{"full_name": "psf/requests"}')):
        data, _ = fetch_github_metadata("psf/requests")

    assert data == {"full_name": "psf/requests"}


def test_rate_limit_headers_parsed() -> None:
    from metadata_observer.github import fetch_github_metadata
    from metadata_observer.http import RateLimitInfo

    headers = {"X-RateLimit-Limit": "60", "X-RateLimit-Remaining": "59", "X-RateLimit-Reset": "1700000000"}
    with patch("metadata_observer.github.urlopen", return_value=_mock_urlopen(b"{}", headers)):
        _, info = fetch_github_metadata("a/b")

    assert isinstance(info, RateLimitInfo)
    assert info.limit == 60
    assert info.remaining == 59


def test_rate_limit_exhausted_raises() -> None:
    from metadata_observer.github import GitHubRateLimitError, fetch_github_metadata

    headers = {"X-RateLimit-Limit": "60", "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1700000000"}
    with (
        patch("metadata_observer.github.urlopen", return_value=_mock_urlopen(b"{}", headers)),
        pytest.raises(GitHubRateLimitError),
    ):
        fetch_github_metadata("a/b")


def test_no_token_no_auth_header(monkeypatch: pytest.MonkeyPatch) -> None:
    from metadata_observer.github import fetch_github_metadata

    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with patch("metadata_observer.github.urlopen", return_value=_mock_urlopen(b"{}")) as mock_open:
        fetch_github_metadata("a/b")

    request = mock_open.call_args[0][0]
    assert "Authorization" not in dict(request.header_items())


def test_cache_write_on_success_only(tmp_path: Path) -> None:
    from metadata_observer.github import fetch_github_metadata

    with patch("metadata_observer.github.urlopen", return_value=_mock_urlopen(b'{"id": 1}')):
        fetch_github_metadata("a/b", cache_dir=tmp_path)

    assert (tmp_path / "github.json").exists()
