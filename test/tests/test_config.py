"""Tests for metadata_observer configuration constants."""

from metadata_observer import conda, config, github, pypi


def test_project_wide_constants() -> None:
    assert config.METADATA_DIR == "metadata"


def test_pypi_constants_live_in_module() -> None:
    assert pypi.URL_PYPI_API == "https://pypi.org/pypi/{package}/json"
    assert isinstance(pypi.TIMEOUT_PYPI_REQUEST, int)
    assert pypi.METADATA_PYPI_FILE == "pypi.json"


def test_github_constants_live_in_module() -> None:
    assert github.URL_GITHUB_API == "https://api.github.com/repos/{repo}"
    assert isinstance(github.TIMEOUT_GITHUB_API, int)
    assert github.GITHUB_API_VERSION == "2022-11-28"


def test_conda_constants_live_in_module() -> None:
    assert "conda-forge" in conda.DEFAULT_CHANNELS
    assert conda.METADATA_CONDA_FILE == "conda.json"
