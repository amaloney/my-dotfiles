"""Conda metadata fetching via `conda search --json`."""

import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CHANNELS = ["conda-forge", "https://repo.anaconda.com/pkgs/main"]
METADATA_CONDA_FILE = "conda.json"
TIMEOUT_CONDA_SEARCH = 60


def fetch_conda_metadata(
    package_name: str, channels: list[str] | None = None, cache_dir: Path | None = None
) -> dict | None:
    """Fetch conda repodata records for a package via `conda search --json`.

    Args:
        package_name: Package name to search for.
        channels: Channels to search; defaults to DEFAULT_CHANNELS.
        cache_dir: Optional directory; on success, writes conda.json into it.

    Returns:
        Parsed repodata dict, or None when the conda CLI is missing, the search
        fails, or the output is not valid JSON.
    """
    channels = channels or DEFAULT_CHANNELS
    cmd = ["conda", "search", "--json", package_name]
    for channel in channels:
        cmd.extend(["-c", channel])

    data = None
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_CONDA_SEARCH, check=True)  # noqa: S603
        data = json.loads(proc.stdout)
    except FileNotFoundError:
        logger.warning("conda CLI not found; skipping conda metadata for %s", package_name)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        logger.warning("conda search failed for %s: %s", package_name, exc)
    except json.JSONDecodeError as exc:
        logger.warning("conda search returned invalid JSON for %s: %s", package_name, exc)

    if data and cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / METADATA_CONDA_FILE).write_text(json.dumps(data, indent=2))

    return data
