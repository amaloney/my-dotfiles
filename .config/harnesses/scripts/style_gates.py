#!/usr/bin/env python3
"""Style gates for Python files, run as Claude Code hooks or from the CLI.

Tiers:
  edit  PostToolUse, only the file just edited (tens of ms)
        ruff format -> ruff check --fix -> AST rules
  stop  SubagentStop / Stop, every file edited this session (once per handoff)
        ruff format -> ruff check --fix -> AST rules + reuse -> pyrefly check

Usage:
  style_gates.py --event edit      # hook: JSON on stdin; exit 2 sends findings to the agent
  style_gates.py --event stop      # hook: exit 2 keeps the (sub)agent working until clean
  style_gates.py PATH [PATH ...]   # CLI / pre-commit / CI: stop tier, exit 1 on findings
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ast_rules import check_file, load_index  # pyrefly: ignore[missing-import]
from naming_check import py_files  # pyrefly: ignore[missing-import]

MAX_STOP_ROUNDS = 3
TOOL_TIMEOUT_SECONDS = 60
CODE_INDEX = os.environ.get("STYLE_GATES_CODE_INDEX", "code_index.json")
FOOTER = (
    "style-gates: fix the findings above (rename, inline, extend existing code, add types). "
    "Suppress only intentional cases, with a reason: `# style:allow`, `# noqa: CODE`, "
    "`# pyrefly: ignore`."
)


WARNED: set[str] = set()


def warn(message: str) -> None:
    if message not in WARNED:
        WARNED.add(message)
        print(f"style-gates: {message}", file=sys.stderr)


def find_tool(name: str) -> str | None:
    """Prefer the tool installed next to this interpreter (the conda env), then PATH."""
    env_tool = Path(sys.executable).parent / name
    return str(env_tool) if env_tool.exists() else shutil.which(name)


def run_tool(name: str, *args: str) -> list[str]:
    executable = find_tool(name)
    if not executable:
        warn(f"{name} not found, gate skipped")
        return []
    try:
        result = subprocess.run(
            [executable, *args],
            capture_output=True,
            text=True,
            timeout=TOOL_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return [f"{name}: timed out after {TOOL_TIMEOUT_SECONDS}s"]
    if result.returncode == 0:
        return []
    output = (result.stdout + result.stderr).strip()
    return [output or f"{name}: exited {result.returncode} with no output"]


def project_root() -> Path:  # style:allow named for clarity
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()


def code_index() -> list[tuple[str, str]] | None:
    index_path = project_root() / CODE_INDEX
    if index_path.is_file():
        return load_index(index_path)
    harness_index = project_root() / ".harness" / CODE_INDEX
    if harness_index.is_file():
        return load_index(harness_index)
    warn(f"code index not found at {index_path}, reuse check skipped")
    return None


def run_gates(files: list[Path], tier: str) -> list[str]:
    names = [str(file) for file in files]

    def ruff_gate() -> list[str]:
        run_tool("ruff", "format", "--quiet", *names)
        return run_tool(
            "ruff",
            "check",
            "--fix",
            "--quiet",
            "--output-format",
            "concise",
            "--extend-select",
            "TID252",
            "--config",
            "lint.flake8-tidy-imports.ban-relative-imports = 'all'",
            *names,
        )

    def style_gate() -> list[str]:
        index = code_index() if tier == "stop" else None
        return [str(finding) for file in files for finding in check_file(file, index)]

    gates: list[tuple[str, Callable[[], list[str]]]] = [
        ("ruff", ruff_gate),
        ("style", style_gate),
    ]
    if tier == "stop":
        gates.append(("pyrefly", lambda: run_tool("pyrefly", "check", *names)))

    report: list[str] = []
    for gate_name, gate in gates:
        problems = gate()
        if problems:
            report += [f"== {gate_name} ==", *problems]
    return report


def state_path(session_id: str) -> Path:  # style:allow named for clarity
    return Path(tempfile.gettempdir()) / f"style-gates-{session_id or 'default'}.json"


def load_state(session_id: str) -> dict:
    try:
        return json.loads(state_path(session_id).read_text())
    except (OSError, ValueError):
        return {"files": [], "stop_rounds": 0}


def save_state(session_id: str, state: dict) -> None:
    state_path(session_id).write_text(json.dumps(state))


def on_edit(payload: dict, state: dict) -> int:
    file_path = payload.get("tool_input", {}).get("file_path", "")
    files = [file for file in py_files([file_path]) if file.is_file()] if file_path else []
    if not files:
        return 0
    edited = str(files[0].resolve())
    if edited not in state["files"]:
        state["files"].append(edited)
    report = run_gates(files, "edit")
    if report:
        print("\n".join([*report, FOOTER]), file=sys.stderr)
        return 2
    return 0


def on_stop(state: dict) -> int:
    files = [Path(file) for file in state["files"] if Path(file).is_file()]
    if not files:
        return 0
    report = run_gates(files, "stop")
    if not report:
        state.update(files=[], stop_rounds=0)
        return 0
    state["stop_rounds"] += 1
    if state["stop_rounds"] > MAX_STOP_ROUNDS:
        state["stop_rounds"] = 0
        print(
            json.dumps(
                {
                    "systemMessage": (
                        f"style-gates: still failing after {MAX_STOP_ROUNDS} rounds; letting the agent stop. "
                        f"Run style_gates.py on: {', '.join(map(str, files))}"
                    )
                }
            )
        )
        return 0
    print("\n".join([*report, FOOTER]), file=sys.stderr)
    return 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", choices=["edit", "stop"], help="run as a Claude Code hook")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()

    if args.event is None:
        files = [file for file in py_files(args.paths) if file.is_file()]
        report = run_gates(files, "stop") if files else []
        if report:
            print("\n".join([*report, FOOTER]), file=sys.stderr)
        return 1 if report else 0

    payload = json.load(sys.stdin)
    session_id = payload.get("session_id", "")
    state = load_state(session_id)
    status = on_edit(payload, state) if args.event == "edit" else on_stop(state)
    save_state(session_id, state)
    return status


if __name__ == "__main__":
    sys.exit(main())
