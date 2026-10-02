"""GitHub API client with rate limit handling."""

import json
import logging
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from metadata_observer.http import RateLimitError, RateLimitInfo, parse_rate_limit

logger = logging.getLogger(__name__)

URL_GITHUB_API = "https://api.github.com/repos/{repo}"
TIMEOUT_GITHUB_API = 30
GITHUB_API_VERSION = "2022-11-28"
METADATA_GITHUB_FILE = "github.json"


class GitHubRateLimitError(RateLimitError):
    """GitHub rate limit exhausted."""

    def __init__(self, reset_timestamp: int) -> None:
        """Initialize with GitHub as the resource name.

        Args:
            reset_timestamp: Unix timestamp when the limit resets.
        """
        super().__init__(reset_timestamp, resource="GitHub")


def build_request(repo: str) -> Request:
    """Build an authenticated-if-possible GitHub API request.

    Args:
        repo: Repository as "owner/name".

    Returns:
        urllib Request with Accept and API-version headers; Authorization
        header added when the GITHUB_TOKEN environment variable is set.
    """
    request = Request(URL_GITHUB_API.format(repo=repo))  # noqa: S310 — URL is a fixed https constant
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", GITHUB_API_VERSION)
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    return request


def fetch_github_metadata(repo: str, cache_dir: Path | None = None) -> tuple[dict | None, RateLimitInfo | None]:
    """Fetch GitHub repo metadata, optionally caching to disk.

    Args:
        repo: Repository as "owner/name".
        cache_dir: Optional directory; on success, writes github.json into it.

    Returns:
        Tuple of (metadata dict or None on failure, parsed rate-limit info or
        None when the response carried no rate-limit headers).

    Raises:
        GitHubRateLimitError: When the rate limit is exhausted.
    """
    info: RateLimitInfo | None = None
    data: dict | None = None
    try:
        with urlopen(build_request(repo), timeout=TIMEOUT_GITHUB_API) as response:  # noqa: S310
            info = parse_rate_limit(response.headers, prefix="X-RateLimit")
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

    return data, info
