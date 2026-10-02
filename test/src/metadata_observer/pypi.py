"""PyPI metadata fetching with optional disk caching."""

import json
import logging
import re
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

URL_PYPI_API = "https://pypi.org/pypi/{package}/json"
TIMEOUT_PYPI_REQUEST = 30
METADATA_PYPI_FILE = "pypi.json"


def fetch_pypi_metadata(package_name: str, cache_dir: Path | None = None) -> dict | None:
    """Fetch PyPI metadata for a package, optionally caching to disk.

    Args:
        package_name: Package name on PyPI; normalized per PEP 503 before fetching.
        cache_dir: Optional directory; on success, writes pypi.json into it.

    Returns:
        PyPI JSON metadata dict, or None on any fetch/parse failure.
    """
    name = re.sub(r"[-_.]+", "-", package_name).lower()  # PEP 503 normalization
    data = None
    try:
        response = requests.get(URL_PYPI_API.format(package=name), timeout=TIMEOUT_PYPI_REQUEST)
        if response.ok:
            data = response.json()
        else:
            logger.warning("PyPI fetch failed for %s: HTTP %s", name, response.status_code)
    except Exception as exc:
        logger.warning("PyPI fetch failed for %s: %s", name, exc)

    if data and cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / METADATA_PYPI_FILE).write_text(json.dumps(data, indent=2))

    return data
