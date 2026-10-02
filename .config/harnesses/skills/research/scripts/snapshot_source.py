"""Usage: python3 snapshot_source.py <url> [--dir sources] [--log _meta] [--topic t] [--note n]

Downloads a URL to <dir>/<sha256-12>.md and appends a search-log row to
<log>/<today>.md."""

import hashlib
import sys
import urllib.request
from datetime import date
from pathlib import Path


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def log_row(logdir: Path, url: str, snapshot: Path, topic: str, note: str) -> None:
    logdir.mkdir(parents=True, exist_ok=True)
    f = logdir / f"{date.today().isoformat()}.md"
    header = "| Source | Topic | Useful | Notes |\n| --- | --- | --- | --- |\n"
    row = f"| {url} | {topic} | Yes | {note}; snapshot: {snapshot} |\n"
    text = f.read_text(encoding="utf-8") if f.exists() else header
    f.write_text(text + row, encoding="utf-8")


def flag(argv: list[str], name: str, default: str) -> str:
    return argv[argv.index(name) + 1] if name in argv else default


def main(argv: list[str]) -> None:
    if len(argv) < 2:
        sys.exit(__doc__)
    url = argv[1]
    data = fetch(url)
    outdir = Path(flag(argv, "--dir", "sources"))
    outdir.mkdir(parents=True, exist_ok=True)
    snapshot = outdir / f"{hashlib.sha256(data).hexdigest()[:12]}.md"
    snapshot.write_bytes(data)
    log_row(Path(flag(argv, "--log", "_meta")), url, snapshot,
            flag(argv, "--topic", "misc"), flag(argv, "--note", "snapshot"))
    print(snapshot)


if __name__ == "__main__":
    main(sys.argv)
