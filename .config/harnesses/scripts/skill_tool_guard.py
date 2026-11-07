#!/usr/bin/env python3
"""PreToolUse hook: enforce allowed-tools from skill frontmatter.

Receives JSON via stdin: {"tool_name": "Edit", "tool_input": {...}}
Reads the most recently loaded skill from .harness/session/loaded_skills.txt.
If the skill has `allowed-tools` in frontmatter, blocks unauthorized tools.

Exit codes:
  0 = allow (tool permitted or no restriction)
  2 = block (tool not in allowed-tools list)
"""

import json
import os
import sys
from pathlib import Path

import yaml

SKILLS_DIR = Path.home() / ".config/harnesses/skills"


def parse_frontmatter(skill_path: Path) -> dict:
    """Extract YAML frontmatter from a skill file."""
    content = skill_path.read_text()
    if not content.startswith("---"):
        return {}

    end = content.find("\n---", 3)
    if end == -1:
        return {}

    frontmatter = content[3:end].strip()
    try:
        return yaml.safe_load(frontmatter) or {}
    except yaml.YAMLError:
        return {}


def resolve_skill_path(entry: str) -> Path | None:
    """Resolve a sentinel entry to a SKILL.md path."""
    entry = entry.strip()
    if not entry:
        return None

    if entry.startswith("skill:"):
        skill_name = entry[6:]
        candidates = [
            SKILLS_DIR / skill_name / "SKILL.md",
            SKILLS_DIR / skill_name.replace("/", "-") / "SKILL.md",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    path = Path(entry)
    if path.exists() and path.name == "SKILL.md":
        return path

    return None


def get_loaded_skill() -> Path | None:
    """Get the most recently loaded skill from the sentinel file."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    sentinel = Path(project_dir) / ".harness/session/loaded_skills.txt"

    if not sentinel.exists():
        return None

    lines = sentinel.read_text().strip().splitlines()
    if not lines:
        return None

    for line in reversed(lines):
        skill_path = resolve_skill_path(line)
        if skill_path:
            return skill_path

    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_name = data.get("tool_name", "")
    if not tool_name:
        return 0

    skill_path = get_loaded_skill()
    if not skill_path:
        return 0

    frontmatter = parse_frontmatter(skill_path)

    allowed_tools = frontmatter.get("allowed-tools", [])
    if not allowed_tools:
        return 0

    if tool_name in allowed_tools:
        return 0

    denied_tools = frontmatter.get("denied-tools", [])
    if tool_name in denied_tools:
        skill_name = frontmatter.get("name", skill_path.stem)
        print(f"Skill '{skill_name}' explicitly denies tool '{tool_name}'", file=sys.stderr)
        return 2

    skill_name = frontmatter.get("name", skill_path.stem)
    print(
        f"Skill '{skill_name}' only allows: {', '.join(allowed_tools)}. Tool '{tool_name}' is not permitted.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
