#!/usr/bin/env python3
"""Render a chat-provenance daily log into a readable session narrative on stdout."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from log_entry import parse_entries
from shared import find_repo_root

MAX_ASSISTANT_LINES = 8


def group_sessions(entries: list[dict]) -> list[dict]:
    groups: dict[str, dict] = {}
    order: list[str] = []
    for entry in entries:
        key = entry["meta"].get("session") or "(ungrouped)"
        if key not in groups:
            groups[key] = {"id": key, "goal": "", "outcome": "", "entries": []}
            order.append(key)
        group = groups[key]
        if entry["kind"] == "session":
            for line in entry["content"].splitlines():
                if line.startswith("goal: "):
                    group["goal"] = line[6:]
                elif line.startswith("outcome: "):
                    group["outcome"] = line[9:]
        else:
            group["entries"].append(entry)
    return [groups[k] for k in order]


def quote(text: str, prefix: str = "> ") -> str:
    return "\n".join(prefix + line for line in text.splitlines())


def render_entry(entry: dict, date_str: str) -> str:
    kind, agent, time = entry["kind"], entry["meta"].get("agent", "?"), entry["time"]
    content = entry["content"]
    label = f"### {time} — {kind} ({agent})"
    if kind == "assistant":
        lines = content.splitlines()
        if len(lines) > MAX_ASSISTANT_LINES:
            shown = "\n".join(lines[:MAX_ASSISTANT_LINES])
            rest = len(lines) - MAX_ASSISTANT_LINES
            return f"{label}\n\n{shown}\n\n*… {rest} more lines — see {date_str}.md#{time}*"
        return f"{label}\n\n{content}"
    if kind == "user":
        return f"{label}\n\n{quote(content)}"
    if kind == "action":
        first = content.splitlines()[0] if content.strip() else "(empty action)"
        return f"- **{time}** {first}"
    return f"{label}\n\n{content}"


def render(date_str: str, text: str, session_filter: str | None) -> str:
    entries = parse_entries(text)
    groups = group_sessions(entries)
    if session_filter:
        groups = [g for g in groups if g["id"] == session_filter]
    out = [f"# {date_str} — session narrative\n"]
    for group in groups:
        if group["id"] != "(ungrouped)":
            out.append(f"## Session {group['id']}\n")
            if group["goal"]:
                out.append(f"**goal:** {group['goal']}")
            if group["outcome"]:
                out.append(f"**outcome:** {group['outcome']}")
            out.append("")
        elif group["entries"]:
            out.append("## Ungrouped entries\n")
        entries_of = group["entries"]
        decisions = [e for e in entries_of if e["kind"] == "decision"]
        actions = [e for e in entries_of if e["kind"] == "action"]
        sources = [e for e in entries_of if e["kind"] == "source"]
        dialogue = [e for e in entries_of if e["kind"] in ("user", "assistant", "summary")]
        for entry in dialogue:
            out.append(render_entry(entry, date_str))
            out.append("")
        if decisions:
            out.append("### Decisions\n")
            for entry in decisions:
                chose = re.search(r"(?m)^chose: (.+)$", entry["content"])
                first = entry["content"].splitlines()[0] if entry["content"] else "(empty)"
                out.append(f"- **{entry['time']}** {chose.group(1) if chose else first}")
            out.append("")
        if actions:
            out.append("### Actions\n")
            for entry in actions:
                out.append(render_entry(entry, date_str))
            out.append("")
        if sources:
            out.append("### Sources\n")
            for entry in sources:
                src = re.search(r"(?m)^source: (.+)$", entry["content"])
                cap = re.search(r"(?m)^capture: (.+)$", entry["content"])
                if src:
                    out.append(f"- {src.group(1)}" + (f" → {cap.group(1)}" if cap else ""))
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("date", nargs="?", help="YYYY-MM-DD; default today")
    parser.add_argument("--session", default=None, help="render only this session id")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        print("error: not inside a git repo", file=sys.stderr)
        return 1
    date_str = args.date or datetime.now().strftime("%Y-%m-%d")
    daily = repo_root / ".harness" / "chat-provenance" / f"{date_str}.md"
    if not daily.exists():
        print(f"error: no log for {date_str} at {daily}", file=sys.stderr)
        return 1
    sys.stdout.write(render(date_str, daily.read_text(encoding="utf-8"), args.session))
    return 0


if __name__ == "__main__":
    sys.exit(main())
