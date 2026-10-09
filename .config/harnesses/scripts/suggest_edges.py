#!/usr/bin/env python3
"""Skill edge suggestions, drift detection, and human feedback.

Deprecated entry point — use the unified CLI:
    llm-skills-network edges --suggest [skill] [-k 10] [--threshold 0.5]
    llm-skills-network edges --compute-drift [--drop 0.10] [--floor 0.35]
    llm-skills-network edges --snapshot
    llm-skills-network edges --feedback <skill-a> <skill-b> accept|reject

This module still hosts the implementation (imported by the CLI). Module
import is stdlib-only; chromadb is imported lazily inside load_vectors().

State (both gitignored, under ~/.config/harnesses/vectors/):
    edge_scores.json    timestamped snapshots of pairwise scores (drift history)
    edge_feedback.json  human accept/reject decisions per skill pair
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

from llm_skills_network.common import LINK_RE, NEXT_RE, SKILLS_DIR, VECTORS_DIR

UTC = timezone.utc

SCORES_FILE = VECTORS_DIR / "edge_scores.json"
FEEDBACK_FILE = VECTORS_DIR / "edge_feedback.json"
MAX_SNAPSHOTS = 10

SkillPair = tuple[str, str]
Vector = list[float]


def get_known_skills() -> set[str]:
    """All skill names from SKILL.md files."""
    return {
        str(p.parent.relative_to(SKILLS_DIR))
        for p in SKILLS_DIR.glob("**/SKILL.md")
    }


def edit_distance(a: str, b: str) -> int:
    """Levenshtein distance between two strings."""
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for ca in a:
        curr = [prev[0] + 1]
        for j, cb in enumerate(b):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]


def suggest_similar(name: str, known: set[str], max_suggestions: int = 3) -> list[str]:
    """Find similar skill names using edit distance."""
    scored = [(edit_distance(name, k), k) for k in known]
    scored.sort()
    threshold = max(3, len(name) // 2)
    return [k for d, k in scored[:max_suggestions] if d <= threshold]


def validate_skill(name: str, known: set[str]) -> None:
    """Exit with error if skill doesn't exist, suggesting alternatives."""
    if name in known:
        return
    similar = suggest_similar(name, known)
    msg = f"error: unknown skill '{name}'"
    if similar:
        msg += f"\n  did you mean: {', '.join(similar)}?"
    else:
        msg += "\n  run with no args to see all skills, or check spelling"
    sys.exit(msg)


def skill_name_from_path(path: str) -> str:
    """Dir name relative to skills/, e.g. python/recon."""
    return str(Path(path).parent.relative_to(SKILLS_DIR))


def load_edges() -> set[SkillPair]:
    """Existing edges as unordered pairs (a, b) with a < b."""
    edges: set[SkillPair] = set()
    for skill_path in SKILLS_DIR.glob("**/SKILL.md"):
        src = str(skill_path.parent.relative_to(SKILLS_DIR))
        text = skill_path.read_text()
        targets = set(LINK_RE.findall(text)) | set(NEXT_RE.findall(text))
        for tgt in targets:
            if tgt != "done" and tgt != src:
                pair: SkillPair = tuple(sorted((src, tgt)))  # type: ignore[assignment]
                edges.add(pair)
    return edges


def load_vectors() -> dict[str, Vector]:
    """Skill-level embedding = mean of its chunk embeddings, L2-normalized."""
    import chromadb

    if not VECTORS_DIR.exists():
        sys.exit("error: vector index not found\n  run: llm-skills-network build --skill-vectors --rebuild")
    client = chromadb.PersistentClient(path=str(VECTORS_DIR))
    try:
        collection = client.get_collection("skills")
    except ValueError:
        sys.exit("error: collection 'skills' not found\n  run: llm-skills-network build --skill-vectors --rebuild")
    data = collection.get(include=["embeddings", "metadatas"])
    if not data["ids"]:
        sys.exit("error: collection is empty\n  run: llm-skills-network build --skill-vectors --rebuild")

    chunks: dict[str, list[Vector]] = {}
    for meta, emb in zip(data["metadatas"], data["embeddings"], strict=True):
        name = skill_name_from_path(meta.get("path", ""))
        chunks.setdefault(name, []).append(list(emb))

    vectors: dict[str, Vector] = {}
    for name, embs in chunks.items():
        dims = len(embs[0])
        mean = [sum(e[i] for e in embs) / len(embs) for i in range(dims)]
        norm = sum(x * x for x in mean) ** 0.5
        vectors[name] = [x / norm for x in mean] if norm else mean
    return vectors


def pairwise_scores(vectors: dict[str, Vector]) -> dict[str, float]:
    """All unordered pairs as 'a|b' -> cosine similarity."""
    scores: dict[str, float] = {}
    for a, b in combinations(sorted(vectors), 2):
        scores[f"{a}|{b}"] = sum(x * y for x, y in zip(vectors[a], vectors[b], strict=True))
    return scores


def load_json(path: Path, default: Any) -> Any:
    """Load JSON file or return default if missing."""
    if path.exists():
        return json.loads(path.read_text())
    return default


def cmd_snapshot(vectors: dict[str, Vector]) -> None:
    """Record current pairwise scores for drift detection."""
    scores = pairwise_scores(vectors)
    history = load_json(SCORES_FILE, {"snapshots": []})
    history["snapshots"].append(
        {"ts": datetime.now(UTC).isoformat(), "scores": scores}
    )
    history["snapshots"] = history["snapshots"][-MAX_SNAPSHOTS:]
    SCORES_FILE.write_text(json.dumps(history, indent=1))
    print(f"snapshot: {len(scores)} pairs recorded ({len(history['snapshots'])} kept)")


def cmd_suggest(
    vectors: dict[str, Vector],
    edges: set[SkillPair],
    skill: str | None,
    k: int,
    threshold: float,
) -> None:
    """Suggest missing edges based on embedding similarity."""
    if skill:
        validate_skill(skill, set(vectors.keys()))

    scores = pairwise_scores(vectors)
    feedback = load_json(FEEDBACK_FILE, {})
    rejected = {tuple(key.split("|")) for key, v in feedback.items() if v == "reject"}

    candidates: list[tuple[float, str, str]] = []
    for pair, score in scores.items():
        a, b = pair.split("|")
        if skill and skill not in (a, b):
            continue
        if (a, b) in edges:
            continue
        if (a, b) in rejected:
            continue
        if score >= threshold:
            candidates.append((score, a, b))

    candidates.sort(reverse=True)
    if not candidates:
        print("no suggestions above threshold")
        return

    print(f"# missing-edge candidates (threshold {threshold})")
    for score, a, b in candidates[:k]:
        line = f"llm-skills-network edges --feedback {a} {b} accept  # {score:.3f}"
        if feedback.get(f"{a}|{b}") == "accept":
            line += f"  →  accepted: llm-skills-network edges --apply {a} {b}"
        print(line)


def cmd_drift(
    vectors: dict[str, Vector],
    edges: set[SkillPair],
    drop: float,
    floor: float,
) -> None:
    """Detect score drift on existing edges between snapshots."""
    history = load_json(SCORES_FILE, {"snapshots": []})
    if len(history["snapshots"]) < 2:
        sys.exit("error: need 2 snapshots to measure drift\n  rebuild the index after editing skills")
    previous = history["snapshots"][-2]["scores"]
    current = history["snapshots"][-1]["scores"]

    flagged: list[tuple[str, str, float, str]] = []
    print(f"edge drift (drop >= {drop} or score < {floor})")
    print(f"  {history['snapshots'][-2]['ts']} -> {history['snapshots'][-1]['ts']}\n")

    for a, b in sorted(edges):
        pair = f"{a}|{b}"
        if pair not in previous or pair not in current:
            continue
        delta = current[pair] - previous[pair]
        if delta <= -drop:
            print(f"  DRIFT {previous[pair]:.3f} -> {current[pair]:.3f}  ({delta:+.3f})  {a} -> {b}")
            flagged.append((a, b, current[pair], "drift"))
        elif current[pair] < floor:
            print(f"  WEAK  {current[pair]:.3f}  (below floor)  {a} -> {b}")
            flagged.append((a, b, current[pair], "weak"))

    if not flagged:
        print("  no drift on existing edges")
    else:
        print("\n# consider removing weak/drifted edges:")
        for a, b, score, reason in flagged:
            print(f"llm-skills-network edges --feedback {a} {b} reject  # {score:.3f} ({reason})")


def cmd_feedback(a: str, b: str, decision: str) -> None:
    """Record human accept/reject decision for a skill pair."""
    known = get_known_skills()
    validate_skill(a, known)
    validate_skill(b, known)
    if a == b:
        sys.exit(f"error: cannot create self-edge: {a}")
    pair = "|".join(sorted((a, b)))
    feedback = load_json(FEEDBACK_FILE, {})
    feedback[pair] = decision
    FEEDBACK_FILE.write_text(json.dumps(feedback, indent=1, sort_keys=True))
    print(f"recorded: {pair} -> {decision}")


def main() -> None:
    """Deprecated shim: delegate to the unified CLI."""
    from llm_skills_network.cli import main as cli_main

    print("deprecated: use llm-skills-network edges ...", file=sys.stderr)
    argv = sys.argv[1:]
    if not argv:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    mapping = {
        "suggest": ["edges", "--suggest"],
        "drift": ["edges", "--compute-drift"],
        "snapshot": ["edges", "--snapshot"],
        "feedback": ["edges", "--feedback"],
    }
    head = argv[0]
    if head not in mapping:
        sys.exit(f"error: unknown subcommand '{head}'\n{__doc__}")
    sys.exit(cli_main(mapping[head] + argv[1:]))


if __name__ == "__main__":
    main()
