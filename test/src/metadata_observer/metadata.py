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


def fetch_metadata(package_name: str, github_repo: str | None = None, cache_dir: Path | None = None) -> PackageMetadata:
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


def recipe_render_context(metadata: PackageMetadata) -> dict[str, str]:
    """Derive the meta.yaml.j2 stage-2 render context from harvested metadata.

    Provenance: name/version/summary/home/license/description/urls come from the
    PyPI payload (about block); sha256 from the PyPI sdist digest (source block);
    requirements/test keys default to empty strings until a conda-forge feedstock
    source is harvested (requirements block).

    Args:
        metadata: Aggregated package metadata. The pypi field is required.

    Returns:
        Substitution map for `string.Template.safe_substitute` against meta.yaml.j2.

    Raises:
        ValueError: When no PyPI metadata was harvested.
    """
    if not metadata.pypi:
        raise ValueError(f"recipe context requires PyPI metadata for {metadata.name}")

    info = metadata.pypi["info"]
    name = info["name"]
    urls = metadata.pypi.get("urls", [])
    sdists = [u for u in urls if u.get("packagetype") == "sdist"]
    sdist = sdists[0] if sdists else {}
    project_urls = info.get("project_urls") or {}

    return {
        "name": name,
        "version": info["version"],
        "sha256": sdist.get("digests", {}).get("sha256", ""),
        "noarch": "",
        "skip": "",
        "build_deps": "",
        "run_deps": "",
        "import_name": name.replace("-", "_"),
        "home_url": info.get("home_page") or "",
        "license_id": info.get("license") or "",
        "license_family": "",
        "license_file": "",
        "summary": info.get("summary") or "",
        "description": info.get("description") or "",
        "dev_url": project_urls.get("Source", ""),
        "doc_url": project_urls.get("Documentation", ""),
        "zendesk_ticket": "",
    }
