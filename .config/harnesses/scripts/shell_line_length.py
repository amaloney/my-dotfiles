#!/usr/bin/env python3
"""Check line length in shell scripts (bash, PowerShell, batch).

Usage:
  shell_line_length.py --event edit   # hook: JSON on stdin
  shell_line_length.py PATH [PATH...] # CLI: check files directly
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MAX_LINE_LENGTH = 120
SHELL_EXTENSIONS = {".sh", ".bash", ".ps1", ".psm1", ".psd1", ".bat", ".cmd"}


def check_file(file_path: Path) -> list[str]:
    """Return list of line length violations."""
    if file_path.suffix.lower() not in SHELL_EXTENSIONS:
        return []
    if not file_path.is_file():
        return []

    violations = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    for line_num, line in enumerate(content.splitlines(), start=1):
        length = len(line)
        if length > MAX_LINE_LENGTH:
            preview = line[:60] + "..." if len(line) > 63 else line
            violations.append(f"{file_path}:{line_num}: line too long ({length} > {MAX_LINE_LENGTH}): {preview}")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", choices=["edit"], help="run as a Claude Code hook")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()

    if args.event == "edit":
        payload = json.load(sys.stdin)
        file_path = payload.get("tool_input", {}).get("file_path", "")
        files = [Path(file_path)] if file_path else []
    else:
        files = [Path(path) for path in args.paths]

    violations = []
    for file in files:
        violations.extend(check_file(file))

    if violations:
        print("\n".join(violations), file=sys.stderr)  # noqa: T201
        print(  # noqa: T201
            f"shell-line-length: refactor lines over {MAX_LINE_LENGTH} chars "
            "(use variables, string concatenation, or line continuation)",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
