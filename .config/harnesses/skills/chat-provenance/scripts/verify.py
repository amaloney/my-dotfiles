#!/usr/bin/env python3
"""Verify the per-entry hash chain and seq monotonicity of daily chat-provenance logs."""

import argparse
import hashlib
import sys
from datetime import datetime
from pathlib import Path

from log_entry import ENTRY_RE, parse_entries
from shared import find_repo_root


def verify_file(path: Path) -> tuple[list[str], int, int]:
    """Return (problems, chained_count, legacy_count)."""
    text = path.read_text(encoding="utf-8")
    entries = parse_entries(text)
    first_match = ENTRY_RE.search(text)
    pre_entry_basis = text[: first_match.start()].rstrip() if first_match else text.rstrip()

    problems: list[str] = []
    chained = legacy = 0
    prev_seq: int | None = None
    prev_block: str | None = None
    for entry in entries:
        meta = entry["meta"]
        seq = meta.get("seq")
        prev = meta.get("prev")
        if seq is None and prev is None:
            legacy += 1
            prev_block = entry["block"]
            continue
        chained += 1
        label = f"{path.name}#{entry.get('time')} seq {seq}"
        if seq is not None:
            if prev_seq is not None and int(seq) <= prev_seq:
                problems.append(f"{label}: seq not monotonic (prev {prev_seq})")
            prev_seq = int(seq)
        if prev is not None:
            expected = prev.removeprefix("sha256:")
            basis = prev_block if prev_block is not None else pre_entry_basis
            actual = hashlib.sha256(basis.encode("utf-8")).hexdigest()
            if actual != expected:
                problems.append(f"{label}: chain break (want {expected[:12]}…, got {actual[:12]}…)")
        prev_block = entry["block"]
    return problems, chained, legacy


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("date", nargs="?", help="YYYY-MM-DD; default today; use 'all' for every log")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        print("error: not inside a git repo", file=sys.stderr)
        return 1
    log_dir = repo_root / ".harness" / "chat-provenance"
    if args.date == "all":
        targets = sorted(log_dir.glob("????-??-??.md"))
    else:
        date_str = args.date or datetime.now().strftime("%Y-%m-%d")
        targets = [log_dir / f"{date_str}.md"]
    missing = [t for t in targets if not t.exists()]
    if missing:
        print(f"error: no log at {missing[0]}", file=sys.stderr)
        return 1

    all_problems: list[str] = []
    for target in targets:
        problems, chained, legacy = verify_file(target)
        all_problems.extend(problems)
        print(f"{target.name}: {chained} chained, {legacy} legacy, {len(problems)} problems")
    for problem in all_problems:
        print(f"  FAIL {problem}")
    return 1 if all_problems else 0


if __name__ == "__main__":
    sys.exit(main())
