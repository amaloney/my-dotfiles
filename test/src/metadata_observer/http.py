"""Generic HTTP API helpers: rate-limit parsing shared across providers."""

import time
from collections.abc import Mapping
from dataclasses import dataclass

RATE_LIMIT_BUFFER = 5


@dataclass
class RateLimitInfo:
    """Rate-limit state for a resource: limit, remaining, reset_timestamp, used."""

    limit: int
    remaining: int
    reset_timestamp: int
    used: int = 0

    # Property semantics are non-obvious (buffer threshold, clamped at zero) — keep terse docs.
    @property
    def is_exhausted(self) -> bool:
        """True when remaining requests are at or below the safety buffer."""
        return self.remaining <= RATE_LIMIT_BUFFER

    @property
    def seconds_until_reset(self) -> int:
        """Seconds until window reset; clamped to zero."""
        return max(0, self.reset_timestamp - int(time.time()))


class RateLimitError(Exception):
    """Raised when a resource's rate limit is exhausted.

    Args:
        reset_timestamp: Unix timestamp when the limit resets.
        resource: Name of the rate-limited resource (e.g. "GitHub", "anaconda.org").
    """

    def __init__(self, reset_timestamp: int, resource: str) -> None:
        self.reset_timestamp = reset_timestamp
        self.resource = resource
        super().__init__(f"{resource} rate limit exhausted; resets in {max(0, reset_timestamp - int(time.time()))}s")


def parse_rate_limit(headers: Mapping[str, str], prefix: str) -> RateLimitInfo | None:
    """Parse rate-limit headers into RateLimitInfo.

    Args:
        headers: Response headers.
        prefix: Header name prefix, e.g. "X-RateLimit" for GitHub's
            X-RateLimit-Limit/Remaining/Reset trio.

    Returns:
        RateLimitInfo when the prefixed headers are present and parseable, else None.
    """
    if f"{prefix}-Remaining" not in headers:
        return None
    try:
        return RateLimitInfo(
            limit=int(headers.get(f"{prefix}-Limit", 0)),
            remaining=int(headers.get(f"{prefix}-Remaining", 0)),
            reset_timestamp=int(headers.get(f"{prefix}-Reset", 0)),
        )
    except (TypeError, ValueError):
        return None
