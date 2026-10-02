"""Constants for metadata acquisition."""

URL_PYPI_API = "https://pypi.org/pypi/{package}/json"
TIMEOUT_PYPI_REQUEST = 30
METADATA_PYPI_FILE = "pypi.json"

URL_GITHUB_API = "https://api.github.com/repos/{repo}"
TIMEOUT_GITHUB_API = 30
GITHUB_API_VERSION = "2022-11-28"

DEFAULT_CHANNELS = ["conda-forge", "https://repo.anaconda.com/pkgs/main"]
METADATA_CONDA_FILE = "conda.json"
METADATA_GITHUB_FILE = "github.json"

METADATA_DIR = "metadata"
