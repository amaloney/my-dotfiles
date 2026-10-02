"""Tests for the generic HTTP rate-limit machinery."""

from metadata_observer.http import RateLimitError, RateLimitInfo, parse_rate_limit


def test_parse_rate_limit_github_headers() -> None:
    headers = {"X-RateLimit-Limit": "60", "X-RateLimit-Remaining": "59", "X-RateLimit-Reset": "1700000000"}
    info = parse_rate_limit(headers, prefix="X-RateLimit")

    assert info is not None
    assert info.limit == 60
    assert info.remaining == 59
    assert info.reset_timestamp == 1700000000


def test_parse_rate_limit_missing_headers_returns_none() -> None:
    assert parse_rate_limit({}, prefix="X-RateLimit") is None


def test_parse_rate_limit_custom_prefix() -> None:
    headers = {"X-Anaconda-Limit": "100", "X-Anaconda-Remaining": "10", "X-Anaconda-Reset": "1700000000"}
    info = parse_rate_limit(headers, prefix="X-Anaconda")

    assert info is not None
    assert info.limit == 100


def test_is_exhausted_boundary() -> None:
    info = RateLimitInfo(limit=60, remaining=5, reset_timestamp=0)
    assert info.is_exhausted

    info = RateLimitInfo(limit=60, remaining=6, reset_timestamp=0)
    assert not info.is_exhausted


def test_seconds_until_reset_never_negative() -> None:
    info = RateLimitInfo(limit=60, remaining=0, reset_timestamp=0)
    assert info.seconds_until_reset == 0


def test_rate_limit_error_names_resource() -> None:
    error = RateLimitError(reset_timestamp=0, resource="anaconda.org")
    assert "anaconda.org" in str(error)
