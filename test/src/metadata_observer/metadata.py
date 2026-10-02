"""Metadata aggregation across PyPI, conda, and GitHub."""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from metadata_observer.conda import fetch_conda_metadata
from metadata_observer.config import METADATA_DIR
from metadata_observer.github import fetch_github_metadata
from metadata_observer.pypi import fetch_pypi_metadata


@dataclass
class PackageMetadata:
    """Aggregated metadata for a package from all sources."""

    name: str
    pypi: dict | None = None
    conda: dict | None = None
    github: dict | None = None
    fetched_at: datetime = field(default_factory=datetime.now)


def fetch_metadata(
    package_name: str, github_repo: str | None = None, cache_dir: Path | None = None
) -> PackageMetadata:
    """Aggregate metadata from PyPI, conda, and (optionally) GitHub.

    Per-source failures do not fail the aggregate; that source's field is None.
    """
    result = PackageMetadata(
        name=package_name,
        pypi=fetch_pypi_metadata(package_name, cache_dir=cache_dir),
        conda=fetch_conda_metadata(package_name, cache_dir=cache_dir),
        github=fetch_github_metadata(github_repo, cache_dir=cache_dir) if github_repo else None,
    )

    if cache_dir:
        aggregate_dir = cache_dir / METADATA_DIR
        aggregate_dir.mkdir(parents=True, exist_ok=True)
        payload = asdict(result)
        payload["fetched_at"] = result.fetched_at.isoformat()
        (aggregate_dir / "metadata.json").write_text(json.dumps(payload, indent=2))

    return result
