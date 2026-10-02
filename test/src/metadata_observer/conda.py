"""Conda metadata fetching via `conda search --json`."""

import json
import logging
import subprocess
from pathlib import Path

from metadata_observer.config import DEFAULT_CHANNELS, METADATA_CONDA_FILE

logger = logging.getLogger(__name__)

TIMEOUT_CONDA_SEARCH = 60


def fetch_conda_metadata(
    package_name: str, channels: list[str] | None = None, cache_dir: Path | None = None
) -> dict | None:
    """Fetch conda repodata records for a package via `conda search --json`."""
    channels = channels or DEFAULT_CHANNELS
    cmd = ["conda", "search", "--json", package_name]
    for channel in channels:
        cmd.extend(["-c", channel])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_CONDA_SEARCH, check=True)
        data = json.loads(proc.stdout)
    except FileNotFoundError:
        logger.warning("conda CLI not found; skipping conda metadata for %s", package_name)
        return None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        logger.warning("conda search failed for %s: %s", package_name, exc)
        return None
    except json.JSONDecodeError as exc:
        logger.warning("conda search returned invalid JSON for %s: %s", package_name, exc)
        return None

    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / METADATA_CONDA_FILE).write_text(json.dumps(data, indent=2))

    return data
