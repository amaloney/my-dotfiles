"""Stdlib-only shared constants and parsers for llm-skills-network.

Everything here must run under the system python3 (3.9+): heavy deps
(chromadb, sentence-transformers) are imported lazily by callers.
LLM_SKILLS_HOME overrides the harness root (used by tests).
"""

from __future__ import annotations

import os
import re
from pathlib import Path

HARNESS_DIR = (
    Path(os.environ["LLM_SKILLS_HOME"])
    if os.environ.get("LLM_SKILLS_HOME")
    else Path.home() / ".config" / "harnesses"
)
SKILLS_DIR = HARNESS_DIR / "skills"
VECTORS_DIR = HARNESS_DIR / "vectors"
AGENTS_MD = HARNESS_DIR / "AGENTS.md"
CONTRACT_MD = HARNESS_DIR / "handoff-contract.md"

LINK_RE = re.compile(r"\[\[([a-z][a-z0-9/_-]*)\]\]")
NEXT_RE = re.compile(r"next: `?(?:\[\[)?([a-z0-9/_-]+)")

RANK_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|[^|]*\|([^|]*)\|")
RANK_NAME_RE = re.compile(r"`([^`]+)`")


def skill_files(skills_dir: Path = SKILLS_DIR) -> list[Path]:
    return sorted(skills_dir.glob("**/SKILL.md"))


def skill_name(skill_path: Path, skills_dir: Path = SKILLS_DIR) -> str:
    return str(skill_path.parent.relative_to(skills_dir))


def skill_exists(name: str, skills_dir: Path = SKILLS_DIR) -> bool:
    return (skills_dir / name).is_dir() or (skills_dir / f"{name}.md").is_file()


def skill_edges(text: str) -> tuple[set[str], set[str]]:
    """(reference links, next: verdicts) declared in a SKILL.md body."""
    links = set(LINK_RE.findall(text))
    nexts = set(NEXT_RE.findall(text))
    return links, nexts


def mentioned_in(name: str, text: str) -> bool:
    """grep -wF semantics: name appears unwrapped by word characters."""
    return re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", text) is not None


def load_ranks(contract: Path = CONTRACT_MD) -> list[tuple[str, int]]:
    """Parse the handoff-contract Termination rank table.

    Returns (pattern, rank) pairs; patterns ending in '*' are prefix wildcards
    (e.g. `windows/*` ranks every windows/ skill).
    """
    ranks: list[tuple[str, int]] = []
    if not contract.exists():
        return ranks
    for line in contract.read_text(encoding="utf-8").splitlines():
        row = RANK_ROW_RE.match(line.strip())
        if not row:
            continue
        rank = int(row.group(1))
        for name in RANK_NAME_RE.findall(row.group(2)):
            ranks.append((name, rank))
    return ranks


def rank_of(name: str, ranks: list[tuple[str, int]]) -> int | None:
    for pattern, rank in ranks:
        if pattern == name:
            return rank
    for pattern, rank in ranks:
        if pattern.endswith("*") and name.startswith(pattern[:-1]):
            return rank
    return None
