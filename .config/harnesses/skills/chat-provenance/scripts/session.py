#!/usr/bin/env python3
"""Session bookkeeping for chat-provenance.

Markers and summaries are record entries in the daily log. Session manifests
and index.md under sessions/ are pure regenerates — `rebuild` reconstructs
them from the logs; never hand-edit them.
"""

import argparse
import json
import os
import re
import secrets
import sys
from datetime import datetime
from pathlib import Path

from log_entry import append_entry, parse_entries
from save_source import atomic_write
from shared import FileLock, find_repo_root

INDEX_HEADER = (
    "# Chat Provenance Index\n\n"
    "<!-- regenerate with: session.py rebuild — never hand-edit -->\n\n"
    "| Date | Session | Goal | Outcome | Manifest |\n| --- | --- | --- | --- | --- |\n"
)

ACCESS_NOTE = "redaction-policy: shared.py SECRET_PATTERNS"


def log_dir_of(repo_root: Path) -> Path:
    path = repo_root / ".harness" / "chat-provenance"
    path.mkdir(parents=True, exist_ok=True)
    return path


def daily_logs(log_dir: Path) -> list[Path]:
    return sorted(log_dir.glob("????-??-??.md"))


def esc(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def collect_sessions(log_dir: Path) -> dict[str, dict]:
    sessions: dict[str, dict] = {}

    def slot(session_id: str, date: str, time: str | None) -> dict:
        if session_id not in sessions:
            sessions[session_id] = {
                "id": session_id,
                "date": date,
                "goal": "(not recorded)",
                "status": "open",
                "outcome": "(open)",
                "summary": None,
                "basis": None,
                "agents": set(),
                "models": set(),
                "creators": set(),
                "harness": None,
                "entries": 0,
                "bytes": 0,
                "captures": [],
                "first": (date, time or "00:00"),
                "last": (date, time or "00:00"),
            }
        return sessions[session_id]

    for daily in daily_logs(log_dir):
        date = daily.name.removesuffix(".md")
        text = daily.read_text(encoding="utf-8")
        creator_match = re.search(r"(?m)^creator: (.+)$", text)
        harness = creator_match.group(1).strip() if creator_match else None
        for entry in parse_entries(text):
            meta, kind, content = entry["meta"], entry["kind"], entry["content"]
            session_id = meta.get("session")
            if kind == "session":
                marker = dict(line.split(": ", 1) for line in content.splitlines() if ": " in line)
                session_id = marker.get("session", session_id)
                if not session_id:
                    continue
                info = slot(session_id, date, entry["time"])
                if "goal" in marker:
                    info["goal"] = marker["goal"]
                if marker.get("status") == "closed":
                    info["status"] = "closed"
                    info["outcome"] = marker.get("outcome", "(not recorded)")
                if harness:
                    info["harness"] = harness
                continue
            if not session_id:
                continue
            info = slot(session_id, date, entry["time"])
            info["last"] = (date, entry["time"] or info["last"][1])
            info["entries"] += 1
            info["bytes"] += len(entry["block"].encode("utf-8"))
            if meta.get("agent"):
                info["agents"].add(meta["agent"])
            if meta.get("model"):
                info["models"].add(meta["model"])
            if meta.get("attr"):
                info["creators"].add(meta["attr"])
            if harness:
                info["harness"] = harness
            if kind == "source":
                capture = re.search(r"(?m)^capture: (.+)$", content)
                if capture:
                    info["captures"].append(capture.group(1).strip())
            if kind == "summary":
                lines = content.split("\n\n", 1)
                header = dict(line.split(": ", 1) for line in lines[0].splitlines() if ": " in line)
                info["basis"] = header.get("basis", info["basis"])
                if header.get("outcome"):
                    info["outcome"] = header["outcome"]
                    info["status"] = "closed"
                info["summary"] = lines[1].strip() if len(lines) > 1 else "(empty summary)"
    return sessions


def manifest_text(info: dict, rebuild_date: str) -> str:
    first, last = info["first"], info["last"]
    arrangement = f"{first[0]}.md#{first[1]}"
    if last != first:
        arrangement += f"..{last[0]}.md#{last[1]}" if last[0] != first[0] else f"..#{last[1]}"
    gaps = []
    if info["status"] != "closed":
        gaps.append("session not closed")
    if not info["summary"]:
        gaps.append("no summary recorded")
    frontmatter = {
        "reference": f"{info['date']}-{info['id']}",
        "level": "file",
        "title": info["goal"],
        "dates": {"start": f"{first[0]} {first[1]}", "end": f"{last[0]} {last[1]}"},
        "extent": {"entries": info["entries"], "bytes": info["bytes"]},
        "creator": sorted(info["creators"])[0] if info["creators"] else "unrecorded",
        "contributing_agents": sorted(info["agents"]) or ["unrecorded"],
        "admin_history": {
            "harness": info["harness"] or "unrecorded",
            "model": sorted(info["models"])[0] if info["models"] else "unrecorded",
        },
        "scope": info["goal"],
        "arrangement": f"chronological; {arrangement}",
        "access": ACCESS_NOTE,
        "related": {"captures": info["captures"]},
        "appraisal": "; ".join(gaps) if gaps else "none noted",
        "description_control": {
            "described_by": "session.py rebuild",
            "basis": "log-replay",
            "date": rebuild_date,
        },
        "status": info["status"],
    }
    yaml_lines = [json.dumps(k) + ": " + json.dumps(v) for k, v in frontmatter.items()]
    summary = info["summary"] or "(not recorded)"
    basis = f" (basis: {info['basis']})" if info["basis"] else ""
    return (
        "---\n" + "\n".join(yaml_lines) + "\n---\n\n"
        f"# Session {info['id']}\n\n"
        f"## summary{basis}\n\n{summary}\n\n"
        f"## outcome\n\n{info['outcome']}\n"
    )


def rebuild(repo_root: Path) -> None:
    log_dir = log_dir_of(repo_root)
    sessions = collect_sessions(log_dir)
    sessions_dir = log_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    rebuild_date = datetime.now().strftime("%Y-%m-%d")

    expected = set()
    rows = []
    for session_id in sorted(sessions, key=lambda s: (sessions[s]["date"], s)):
        info = sessions[session_id]
        filename = f"{info['date']}-{session_id}.md"
        expected.add(filename)
        atomic_write(sessions_dir / filename, manifest_text(info, rebuild_date))
        rows.append(
            f"| {info['date']} | {esc(session_id)} | {esc(info['goal'])} | "
            f"{esc(info['outcome'])} | sessions/{filename} |\n"
        )
    for stale in sessions_dir.glob("*.md"):
        if stale.name not in expected:
            stale.unlink()
    atomic_write(log_dir / "index.md", INDEX_HEADER + "".join(rows))


def cmd_start(repo_root: Path, args: argparse.Namespace) -> int:
    session_id = args.id or secrets.token_hex(3)
    log_dir = log_dir_of(repo_root)
    with FileLock(log_dir / ".lock"):
        append_entry(
            log_dir,
            "session",
            args.agent,
            f"session: {session_id}\ngoal: {args.goal}\nstatus: open",
            session=session_id,
        )
        rebuild(repo_root)
    print(f"session: {session_id}")
    return 0


def cmd_end(repo_root: Path, args: argparse.Namespace) -> int:
    log_dir = log_dir_of(repo_root)
    with FileLock(log_dir / ".lock"):
        sessions = collect_sessions(log_dir)
        if args.id not in sessions:
            print(f"error: no session {args.id} found in logs", file=sys.stderr)
            return 1
        today = datetime.now().strftime("%Y-%m-%d")
        daily = log_dir / f"{today}.md"
        derived = f"{today} seq (no entries today)"
        if daily.exists():
            seqs = [
                int(e["meta"]["seq"])
                for e in parse_entries(daily.read_text(encoding="utf-8"))
                if e["meta"].get("session") == args.id and e["meta"].get("seq")
            ]
            if seqs:
                derived = f"{today} seq {min(seqs)}..{max(seqs)}"
        summary = args.summary or "(no summary recorded)"
        append_entry(
            log_dir,
            "summary",
            args.agent,
            f"derived_from: {derived}\nbasis: {args.basis}\noutcome: {args.outcome}\n\n{summary}",
            session=args.id,
        )
        append_entry(
            log_dir,
            "session",
            args.agent,
            f"session: {args.id}\noutcome: {args.outcome}\nstatus: closed",
            session=args.id,
        )
        rebuild(repo_root)
    print(f"closed: {log_dir / 'sessions'}")
    return 0


def cmd_replay(repo_root: Path, args: argparse.Namespace) -> int:
    log_dir = log_dir_of(repo_root)
    with FileLock(log_dir / ".lock"):
        sessions = collect_sessions(log_dir)
        if args.id not in sessions:
            print(f"error: no session {args.id} found in logs", file=sys.stderr)
            return 1
        info = sessions[args.id]
        parts = [
            f"goal: {info['goal']}",
            f"span: {info['first'][0]} {info['first'][1]} → {info['last'][0]} {info['last'][1]}",
            f"entries: {info['entries']} across agents {', '.join(sorted(info['agents'])) or 'unrecorded'}",
        ]
        kinds: dict[str, int] = {}
        decisions, actions, sources = [], [], []
        for daily in daily_logs(log_dir):
            for entry in parse_entries(daily.read_text(encoding="utf-8")):
                if entry["meta"].get("session") != args.id:
                    continue
                kinds[entry["kind"]] = kinds.get(entry["kind"], 0) + 1
                if entry["kind"] == "decision":
                    chose = re.search(r"(?m)^chose: (.+)$", entry["content"])
                    decisions.append(chose.group(1) if chose else entry["content"].splitlines()[0])
                elif entry["kind"] == "action":
                    actions.append(entry["content"].splitlines()[0])
                elif entry["kind"] == "source":
                    src = re.search(r"(?m)^source: (.+)$", entry["content"])
                    if src:
                        sources.append(src.group(1))
        parts.append("kinds: " + ", ".join(f"{k}×{n}" for k, n in sorted(kinds.items())))
        if decisions:
            parts.append("decisions: " + "; ".join(decisions))
        if actions:
            parts.append("actions: " + "; ".join(actions[:10]))
        if sources:
            parts.append("sources: " + "; ".join(sources))
        body = "\n".join(parts)
        append_entry(
            log_dir,
            "summary",
            args.agent,
            f"derived_from: log replay across {len(daily_logs(log_dir))} daily log(s)\n"
            f"basis: log-replay\noutcome: {info['outcome']}\n\n{body}",
            session=args.id,
        )
        rebuild(repo_root)
    print(f"replayed: {args.id}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_start = sub.add_parser("start", help="open a session: marker entry + rebuild")
    p_start.add_argument("--goal", default="(not recorded)")
    p_start.add_argument("--id", default=None, help="session id; default random 6-hex")
    p_start.add_argument("--agent", default="main")

    p_end = sub.add_parser("end", help="close: summary record entry + marker + rebuild")
    p_end.add_argument("id", help="session id from start")
    p_end.add_argument("--outcome", default="(not recorded)")
    p_end.add_argument("--summary", default=None)
    p_end.add_argument(
        "--basis",
        default="context-window",
        choices=["context-window", "log-replay"],
        help="what the summary is based on; context-window asserts live authorship",
    )
    p_end.add_argument("--agent", default="main")

    p_replay = sub.add_parser("summarize", help="append a log-replay summary record for a session")
    p_replay.add_argument("id")
    p_replay.add_argument("--replay", action="store_true", required=True)
    p_replay.add_argument("--agent", default="main")

    p_rebuild = sub.add_parser("rebuild", help="regenerate manifests + index from logs")
    p_rebuild.set_defaults(rebuild_only=True)

    args = parser.parse_args()
    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        print("error: not inside a git repo; skipping session bookkeeping", file=sys.stderr)
        return 1
    os.environ.setdefault("CHAT_PROVENANCE_CREATOR", "unknown-harness")
    if args.command == "start":
        return cmd_start(repo_root, args)
    if args.command == "end":
        return cmd_end(repo_root, args)
    if args.command == "summarize":
        return cmd_replay(repo_root, args)
    log_dir = log_dir_of(repo_root)
    with FileLock(log_dir / ".lock"):
        rebuild(repo_root)
    print(f"rebuilt: {log_dir / 'sessions'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
