"""Shared helpers for chat-provenance scripts: repo discovery, redaction, file locking."""

import os
import re
import time
from pathlib import Path

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("openai-key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("github-pat", re.compile(r"ghp_[A-Za-z0-9]{36}")),
]


def find_repo_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def redact_report(content: str) -> tuple[str, list[str]]:
    kinds = []
    for kind, pattern in SECRET_PATTERNS:
        if pattern.search(content):
            kinds.append(kind)
            content = pattern.sub(f"[REDACTED:{kind}]", content)
    return content, kinds


def redact(content: str) -> str:
    return redact_report(content)[0]


class FileLock:
    def __init__(self, lock_path: Path) -> None:
        self._lock_path = lock_path
        self._fd: int | None = None
        self._lockdir: Path | None = None
        try:
            import fcntl  # noqa: F401

            self._use_fcntl = True
        except ImportError:
            self._use_fcntl = False

    def __enter__(self) -> FileLock:
        if self._use_fcntl:
            import fcntl

            self._fd = os.open(self._lock_path, os.O_CREAT | os.O_RDWR, 0o600)
            fcntl.flock(self._fd, fcntl.LOCK_EX)
        else:
            self._lockdir = self._lock_path.with_suffix(".lockdir")
            deadline = time.monotonic() + 30
            while True:
                try:
                    os.mkdir(self._lockdir)
                    break
                except FileExistsError:
                    if time.monotonic() > deadline:
                        raise TimeoutError(f"could not acquire lock {self._lockdir}") from None
                    time.sleep(0.05)
        return self

    def __exit__(self, *exc: object) -> None:
        if self._use_fcntl and self._fd is not None:
            import fcntl

            fcntl.flock(self._fd, fcntl.LOCK_UN)
            os.close(self._fd)
        elif self._lockdir is not None:
            os.rmdir(self._lockdir)
