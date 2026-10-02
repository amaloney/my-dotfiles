"""Tests for conda metadata fetching."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch


def _conda_search_payload() -> dict:
    return {"requests": [{"name": "requests", "version": "2.32.3", "channel": "conda-forge"}]}


def test_fetch_returns_records_on_success() -> None:
    from metadata_observer.conda import fetch_conda_metadata

    proc = MagicMock(returncode=0, stdout=json.dumps(_conda_search_payload()))
    with patch("metadata_observer.conda.subprocess.run", return_value=proc):
        result = fetch_conda_metadata("requests")

    assert result is not None
    assert "requests" in result


def test_cli_missing_returns_none() -> None:
    from metadata_observer.conda import fetch_conda_metadata

    with patch("metadata_observer.conda.subprocess.run", side_effect=FileNotFoundError):
        result = fetch_conda_metadata("requests")

    assert result is None


def test_nonzero_exit_returns_none() -> None:
    from metadata_observer.conda import fetch_conda_metadata

    with patch(
        "metadata_observer.conda.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "conda"),
    ):
        result = fetch_conda_metadata("requests")

    assert result is None


def test_invalid_json_returns_none() -> None:
    from metadata_observer.conda import fetch_conda_metadata

    proc = MagicMock(returncode=0, stdout="not json")
    with patch("metadata_observer.conda.subprocess.run", return_value=proc):
        result = fetch_conda_metadata("requests")

    assert result is None


def test_default_channels_used() -> None:
    from metadata_observer.conda import fetch_conda_metadata
    from metadata_observer.config import DEFAULT_CHANNELS

    proc = MagicMock(returncode=0, stdout=json.dumps(_conda_search_payload()))
    with patch("metadata_observer.conda.subprocess.run", return_value=proc) as mock_run:
        fetch_conda_metadata("requests")

    cmd = mock_run.call_args[0][0]
    for channel in DEFAULT_CHANNELS:
        assert channel in cmd


def test_cache_write_on_success(tmp_path: Path) -> None:
    from metadata_observer.conda import fetch_conda_metadata

    proc = MagicMock(returncode=0, stdout=json.dumps(_conda_search_payload()))
    with patch("metadata_observer.conda.subprocess.run", return_value=proc):
        fetch_conda_metadata("requests", cache_dir=tmp_path)

    assert (tmp_path / "conda.json").exists()
