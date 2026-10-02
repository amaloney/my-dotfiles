"""Package metadata acquisition from PyPI, conda, and GitHub."""

from metadata_observer.metadata import PackageMetadata, fetch_metadata

__all__ = ["PackageMetadata", "fetch_metadata"]
