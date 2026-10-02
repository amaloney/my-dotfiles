"""Tests for the metadata aggregator."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from metadata_observer.metadata import PackageMetadata, fetch_metadata


def test_all_sources_populated() -> None:
    with (
        patch("metadata_observer.metadata.fetch_pypi_metadata", return_value={"info": {}}),
        patch("metadata_observer.metadata.fetch_conda_metadata", return_value={"requests": []}),
        patch("metadata_observer.metadata.fetch_github_metadata", return_value={"full_name": "a/b"}),
    ):
        result = fetch_metadata("requests", github_repo="a/b")

    assert result.pypi == {"info": {}}
    assert result.conda == {"requests": []}
    assert result.github == {"full_name": "a/b"}
    assert isinstance(result.fetched_at, datetime)
    assert result.name == "requests"


def test_one_source_none_others_populated() -> None:
    with (
        patch("metadata_observer.metadata.fetch_pypi_metadata", return_value=None),
        patch("metadata_observer.metadata.fetch_conda_metadata", return_value={"requests": []}),
        patch("metadata_observer.metadata.fetch_github_metadata", return_value={"full_name": "a/b"}),
    ):
        result = fetch_metadata("requests", github_repo="a/b")

    assert result.pypi is None
    assert result.conda is not None
    assert result.github is not None


def test_github_skipped_when_no_repo() -> None:
    with (
        patch("metadata_observer.metadata.fetch_pypi_metadata", return_value={"info": {}}),
        patch("metadata_observer.metadata.fetch_conda_metadata", return_value=None),
        patch("metadata_observer.metadata.fetch_github_metadata") as mock_gh,
    ):
        result = fetch_metadata("requests")

    assert result.github is None
    mock_gh.assert_not_called()


def test_aggregate_cached(tmp_path: Path) -> None:
    import json

    with (
        patch("metadata_observer.metadata.fetch_pypi_metadata", return_value={"info": {}}),
        patch("metadata_observer.metadata.fetch_conda_metadata", return_value=None),
    ):
        fetch_metadata("requests", cache_dir=tmp_path)

    cache_file = tmp_path / "metadata" / "metadata.json"
    assert cache_file.exists()
    cached = json.loads(cache_file.read_text())
    assert cached["name"] == "requests"
    assert cached["pypi"] == {"info": {}}


def test_returns_package_metadata_type() -> None:
    with (
        patch("metadata_observer.metadata.fetch_pypi_metadata", return_value=None),
        patch("metadata_observer.metadata.fetch_conda_metadata", return_value=None),
    ):
        result = fetch_metadata("requests")

    assert isinstance(result, PackageMetadata)
