#!/usr/bin/env python3
"""Claude Code hook bridge: log prompts and final outputs to chat-provenance.

Reads the hook's JSON payload on stdin. Never blocks the session: any failure
exits 0 after a stderr note.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from log_entry import append_entry
from shared import FileLock, find_repo_root, redact

STATE_FILE = ".claude-hook-state.json"


def log(repo_root: Path, kind: str, agent: str, content: str, session: str | None) -> None:
    log_dir = repo_root / ".harness" / "chat-provenance"
    log_dir.mkdir(parents=True, exist_ok=True)
    with FileLock(log_dir / ".lock"):
        append_entry(log_dir, kind, agent, redact(content), session=session)


def last_assistant_text(transcript: Path) -> tuple[str | None, str | None, str | None]:
    """Return (message_id, text, model) of the last assistant message with text content."""
    last_id, last_text, last_model = None, None, None
    with transcript.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("type") != "assistant":
                continue
            message = record.get("message", {})
            texts = [
                block.get("text", "")
                for block in message.get("content", [])
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            if any(t.strip() for t in texts):
                last_id = message.get("id") or record.get("uuid")
                last_text = "\n".join(t for t in texts if t.strip())
                last_model = message.get("model")
    return last_id, last_text, last_model


def load_state(log_dir: Path) -> dict[str, str]:
    state_path = log_dir / STATE_FILE
    if state_path.exists():
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_state(log_dir: Path, state: dict[str, str]) -> None:
    (log_dir / STATE_FILE).write_text(json.dumps(state, indent=1), encoding="utf-8")


def main() -> int:
    os.environ.setdefault("CHAT_PROVENANCE_CREATOR", "claude-code")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", required=True, choices=["user", "stop", "subagent"])
    args = parser.parse_args()

    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        print("chat-provenance: bad hook JSON; skipping", file=sys.stderr)
        return 0

    cwd = payload.get("cwd")
    start = Path(cwd) if cwd and Path(cwd).is_dir() else Path.cwd()
    repo_root = find_repo_root(start)
    if repo_root is None:
        return 0
    session = payload.get("session_id")

    if args.event == "user":
        prompt = payload.get("prompt", "")
        if prompt.strip():
            log(repo_root, "user", "main", prompt, session)
        return 0

    transcript = payload.get("transcript_path")
    if not transcript or not Path(transcript).is_file():
        return 0
    message_id, text, model = last_assistant_text(Path(transcript))
    if not text:
        return 0

    log_dir = repo_root / ".harness" / "chat-provenance"
    log_dir.mkdir(parents=True, exist_ok=True)
    with FileLock(log_dir / ".lock"):
        state = load_state(log_dir)
        state_key = f"{session}:{args.event}"
        if message_id and state.get(state_key) == message_id:
            return 0
        agent = "main" if args.event == "stop" else "subagent"
        append_entry(log_dir, "assistant", agent, redact(text), session=session, model=model)
        if message_id:
            state[state_key] = message_id
            save_state(log_dir, state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
