"""GitHub API client with rate limit handling."""

import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from metadata_observer.config import GITHUB_API_VERSION, METADATA_GITHUB_FILE, TIMEOUT_GITHUB_API, URL_GITHUB_API

logger = logging.getLogger(__name__)

RATE_LIMIT_BUFFER = 5


@dataclass
class RateLimitInfo:
    """GitHub API rate limit information."""

    limit: int
    remaining: int
    reset_timestamp: int
    used: int = 0

    @property
    def is_exhausted(self) -> bool:
        return self.remaining <= RATE_LIMIT_BUFFER

    @property
    def seconds_until_reset(self) -> int:
        return max(0, self.reset_timestamp - int(time.time()))


class GitHubRateLimitError(Exception):
    """Raised when the GitHub API rate limit is exhausted."""

    def __init__(self, reset_timestamp: int) -> None:
        self.reset_timestamp = reset_timestamp
        super().__init__(f"GitHub rate limit exhausted; resets in {max(0, reset_timestamp - int(time.time()))}s")


def _parse_rate_limit(headers) -> RateLimitInfo | None:
    if "X-RateLimit-Remaining" not in headers:
        return None
    try:
        return RateLimitInfo(
            limit=int(headers.get("X-RateLimit-Limit", 0)),
            remaining=int(headers.get("X-RateLimit-Remaining", 0)),
            reset_timestamp=int(headers.get("X-RateLimit-Reset", 0)),
        )
    except (TypeError, ValueError):
        return None


def _build_request(repo: str) -> Request:
    request = Request(URL_GITHUB_API.format(repo=repo))
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", GITHUB_API_VERSION)
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    return request


def fetch_github_metadata(
    repo: str, cache_dir: Path | None = None, _return_rate_limit: bool = False
) -> dict | None | tuple[dict | None, RateLimitInfo | None]:
    """Fetch GitHub repo metadata, optionally caching to disk.

    Raises GitHubRateLimitError when the rate limit is exhausted.
    """
    info: RateLimitInfo | None = None
    data: dict | None = None
    try:
        with urlopen(_build_request(repo), timeout=TIMEOUT_GITHUB_API) as response:
            info = _parse_rate_limit(response.headers)
            if info and info.is_exhausted:
                raise GitHubRateLimitError(info.reset_timestamp)
            data = json.loads(response.read().decode())
    except GitHubRateLimitError:
        raise
    except HTTPError as exc:
        logger.warning("GitHub fetch failed for %s: HTTP %s", repo, exc.code)
    except Exception as exc:
        logger.warning("GitHub fetch failed for %s: %s", repo, exc)

    if data and cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / METADATA_GITHUB_FILE).write_text(json.dumps(data, indent=2))

    if _return_rate_limit:
        return data, info
    return data
