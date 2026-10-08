#!/usr/bin/env python3
"""Append a verbatim chat-provenance entry to .harness/chat-provenance/YYYY-MM-DD.md.

Format v2: true append-only under flock; per-entry metadata carries seq, attr
(human creator), model, repo state, and a prev-entry hash chain.
"""

import argparse
import getpass
import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from shared import FileLock, find_repo_root, redact_report

FRONTMATTER_TEMPLATE = """---
date: {date}
type: chat-provenance-log
creator: {creator}
---

# Chat Provenance — {date}
"""

KINDS = ["user", "assistant", "action", "decision", "source", "summary", "session"]

ENTRY_RE = re.compile(r"(?m)^## (\w+)[^\n]*$")
TIME_RE = re.compile(r"(?m)^# (\d{2}:\d{2})$")


def parse_entries(text: str) -> list[dict]:
    """Parse a daily log into entries: kind, time, meta dict, content, raw block."""
    times = list(TIME_RE.finditer(text))

    def time_at(pos: int) -> str | None:
        found = None
        for match in times:
            if match.start() < pos:
                found = match.group(1)
            else:
                break
        return found

    matches = list(ENTRY_RE.finditer(text))
    entries = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        segment = text[match.start() : end]
        heading = TIME_RE.search(segment)
        if heading:
            segment = segment[: heading.start()]
        block = segment.rstrip()
        meta: dict[str, str] = {}
        content = ""
        meta_match = re.search(r"(?m)^agent: [^\n]*$", segment)
        if meta_match:
            for part in meta_match.group(0).split(" | "):
                if ": " in part:
                    key, value = part.split(": ", 1)
                    meta[key.strip()] = value.strip()
            fence = re.search(r"````markdown\n([\s\S]*?)\n````", segment)
            content = fence.group(1) if fence else segment[meta_match.end() :].strip()
        entries.append(
            {
                "kind": match.group(1),
                "time": time_at(match.start()),
                "meta": meta,
                "content": content,
                "block": block,
            }
        )
    return entries


def repo_state(repo_root: Path) -> str | None:
    try:
        branch = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        sha = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return None
    return f"{branch}@{sha}" if branch and sha else None


def build_subsection(
    kind: str,
    agent: str,
    content: str,
    session: str | None = None,
    task: str | None = None,
    seq: int | None = None,
    attr: str | None = None,
    model: str | None = None,
    at: str | None = None,
    prev: str | None = None,
    event_time: str | None = None,
) -> str:
    parts = [f"agent: {agent}"]
    if session:
        parts.append(f"session: {session}")
    if task:
        parts.append(f"task: {task}")
    if seq is not None:
        parts.append(f"seq: {seq}")
    if attr:
        parts.append(f"attr: {attr}")
    if model:
        parts.append(f"model: {model}")
    if at:
        parts.append(f"at: {at}")
    if prev:
        parts.append(f"prev: sha256:{prev}")
    if event_time:
        parts.append(f"event: {event_time}")
    return f"## {kind}\n\n{' | '.join(parts)}\n\n````markdown\n{content.rstrip()}\n````\n"


def append_entry(
    log_dir: Path,
    kind: str,
    agent: str,
    content: str,
    session: str | None = None,
    task: str | None = None,
    model: str | None = None,
    event_time: str | None = None,
) -> str:
    """Append under an external or internal lock; caller may hold the flock."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    daily = log_dir / f"{date_str}.md"
    repo_root = log_dir.parent.parent

    attr = os.environ.get("CHAT_PROVENANCE_USER") or _safe_user()
    model = model or os.environ.get("CHAT_PROVENANCE_MODEL") or None
    at = repo_state(repo_root)

    existing = daily.read_text(encoding="utf-8") if daily.exists() else None
    entries = parse_entries(existing) if existing else []
    seq = len(entries) + 1

    if existing is None:
        prefix = FRONTMATTER_TEMPLATE.format(
            date=date_str, creator=os.environ.get("CHAT_PROVENANCE_CREATOR", "unknown-harness")
        )
        prev_basis = (prefix + f"\n# {time_str}").rstrip()
        need_heading = True
    else:
        prev_basis = entries[-1]["block"] if entries else existing.rstrip()
        headings = list(TIME_RE.finditer(existing))
        need_heading = not (headings and headings[-1].group(1) == time_str)
    prev = hashlib.sha256(prev_basis.encode("utf-8")).hexdigest()

    subsection = build_subsection(kind, agent, content, session, task, seq, attr, model, at, prev, event_time)

    if existing is None:
        with daily.open("w", encoding="utf-8") as fh:
            fh.write(prefix + f"\n# {time_str}\n\n{subsection}")
    else:
        chunk = (f"\n# {time_str}\n\n" if need_heading else "\n") + subsection
        with daily.open("a", encoding="utf-8") as fh:
            fh.write(chunk)

    return f"{daily}#{time_str}"


def _safe_user() -> str:
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return "unknown-user"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=["user", "assistant"])
    parser.add_argument(
        "--kind",
        default=None,
        choices=KINDS,
        help="entry kind for the ## heading; defaults to --role",
    )
    parser.add_argument("--agent", required=True, help="agent name, e.g. main, bug, code-hygiene")
    parser.add_argument("--session", default=None, help="session id this entry belongs to")
    parser.add_argument("--task", default=None, help="subagent task id, if applicable")
    parser.add_argument("--model", default=None, help="model id; default CHAT_PROVENANCE_MODEL env")
    parser.add_argument(
        "--event-time",
        default=None,
        help="ISO-8601 time the event occurred, if different from log time",
    )
    args = parser.parse_args()

    content = sys.stdin.read()
    if not content.strip():
        print("error: empty content on stdin", file=sys.stderr)
        return 2

    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        print("error: not inside a git repo; skipping provenance log", file=sys.stderr)
        return 1

    log_dir = repo_root / ".harness" / "chat-provenance"
    log_dir.mkdir(parents=True, exist_ok=True)

    content, redacted_kinds = redact_report(content)
    kind = args.kind or args.role

    with FileLock(log_dir / ".lock"):
        location = append_entry(
            log_dir, kind, args.agent, content, args.session, args.task, args.model, args.event_time
        )
        for redacted in redacted_kinds:
            append_entry(
                log_dir,
                "action",
                args.agent,
                f"redaction: {redacted} pattern matched in the preceding {kind} entry",
                session=args.session,
            )

    print(f"logged: {location}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
