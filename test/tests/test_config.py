"""Tests for metadata_observer configuration constants."""


def test_pypi_constants() -> None:
    from metadata_observer import config

    assert config.URL_PYPI_API == "https://pypi.org/pypi/{package}/json"
    assert isinstance(config.TIMEOUT_PYPI_REQUEST, int)
    assert config.METADATA_PYPI_FILE == "pypi.json"


def test_github_constants() -> None:
    from metadata_observer import config

    assert config.URL_GITHUB_API == "https://api.github.com/repos/{repo}"
    assert isinstance(config.TIMEOUT_GITHUB_API, int)
    assert config.GITHUB_API_VERSION == "2022-11-28"


def test_conda_constants() -> None:
    from metadata_observer import config

    assert "conda-forge" in config.DEFAULT_CHANNELS
    assert config.METADATA_CONDA_FILE == "conda.json"
    assert config.METADATA_DIR == "metadata"
