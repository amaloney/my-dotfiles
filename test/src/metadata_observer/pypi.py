"""PyPI metadata fetching with optional disk caching."""

import json
import logging
import re
from pathlib import Path

import requests

from metadata_observer.config import METADATA_PYPI_FILE, TIMEOUT_PYPI_REQUEST, URL_PYPI_API

logger = logging.getLogger(__name__)


def normalize_name(package_name: str) -> str:
    """Normalize a package name per PEP 503."""
    return re.sub(r"[-_.]+", "-", package_name).lower()


def fetch_pypi_metadata(package_name: str, cache_dir: Path | None = None) -> dict | None:
    """Fetch PyPI metadata for a package, optionally caching to disk."""
    name = normalize_name(package_name)
    try:
        response = requests.get(URL_PYPI_API.format(package=name), timeout=TIMEOUT_PYPI_REQUEST)
        if not response.ok:
            logger.warning("PyPI fetch failed for %s: HTTP %s", name, response.status_code)
            return None
        data = response.json()
    except Exception as exc:
        logger.warning("PyPI fetch failed for %s: %s", name, exc)
        return None

    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / METADATA_PYPI_FILE).write_text(json.dumps(data, indent=2))

    return data
