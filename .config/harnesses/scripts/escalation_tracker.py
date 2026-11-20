#!/usr/bin/env python3
"""Track repeated failure reports and escalate to plan mode + web search on third occurrence.

Runs as a UserPromptSubmit hook. When the user says "still does not work" (or similar)
three times, injects guidance to enter plan mode and use WebSearch.

Usage:
  escalation_tracker.py  # hook: JSON on stdin with prompt field
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

ESCALATION_THRESHOLD = 3

FRUSTRATION_PATTERNS = [
    r"still\s+(does\s*n[o']?t|doesn['\s]t|not)\s+work",
    r"still\s+broken",
    r"still\s+failing",
    r"same\s+(error|problem|issue)",
    r"didn['\s]t\s+(work|fix|help)",
    r"doesn['\s]t\s+(work|fix|help)",
    r"not\s+working",
    r"that\s+didn['\s]t\s+(work|fix|help)",
]

COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in FRUSTRATION_PATTERNS]


def state_path(session_id: str) -> Path:  # style:allow named for clarity, matches style_gates.py
    return Path(tempfile.gettempdir()) / f"escalation-{session_id or 'default'}.json"


def load_state(session_id: str) -> dict:
    """Load session state from temp file."""
    try:
        return json.loads(state_path(session_id).read_text())
    except (OSError, ValueError):
        return {"frustration_count": 0}


def save_state(session_id: str, state: dict) -> None:
    """Persist session state to temp file."""
    state_path(session_id).write_text(json.dumps(state))


def main() -> int:
    payload = json.load(sys.stdin)
    session_id = payload.get("session_id", "")
    prompt = payload.get("prompt", "")

    state = load_state(session_id)

    if any(pattern.search(prompt) for pattern in COMPILED_PATTERNS):
        state["frustration_count"] += 1
        save_state(session_id, state)

        if state["frustration_count"] >= ESCALATION_THRESHOLD:
            state["frustration_count"] = 0
            save_state(session_id, state)
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "UserPromptSubmit",
                            "additionalContext": (
                                "User has reported failure 3+ times for the same issue. "
                                "STOP attempting fixes. Enter plan mode (EnterPlanMode tool), "
                                "then use WebSearch to research the error/symptoms before proposing "
                                "another solution. Reference: debugging skill Phase 3 - hypothesise "
                                "with external evidence before testing."
                            ),
                        },
                    },
                ),
            )
    else:
        if state["frustration_count"] > 0:
            state["frustration_count"] = 0
            save_state(session_id, state)

    return 0


if __name__ == "__main__":
    sys.exit(main())
