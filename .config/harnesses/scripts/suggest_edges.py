#!/usr/bin/env python3
"""Skill edge suggestions, drift detection, and human feedback.

Reads skill-level embeddings from the vector store (mean of each skill's chunk
embeddings) and the existing edge set from SKILL.md files ([[links]] + next:
verdicts, same rules as skill-graph.sh).

Usage:
    python suggest_edges.py suggest [skill] [-k 10] [--threshold 0.5]
    python suggest_edges.py drift [--drop 0.10] [--floor 0.35]
    python suggest_edges.py snapshot
    python suggest_edges.py feedback <skill-a> <skill-b> accept|reject

State (both gitignored, under ~/.config/harnesses/vectors/):
    edge_scores.json    timestamped snapshots of pairwise scores (drift history)
    edge_feedback.json  human accept/reject decisions per skill pair
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import Any

import chromadb
import numpy as np

SKILLS_DIR = Path.home() / ".config" / "harnesses" / "skills"
VECTORS_DIR = Path.home() / ".config" / "harnesses" / "vectors"
SCORES_FILE = VECTORS_DIR / "edge_scores.json"
FEEDBACK_FILE = VECTORS_DIR / "edge_feedback.json"
MAX_SNAPSHOTS = 10

LINK_RE = re.compile(r"\[\[([a-z][a-z0-9/_-]*)\]\]")
NEXT_RE = re.compile(r"next: `?(?:\[\[)?([a-z0-9/_-]+)")

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
    if not VECTORS_DIR.exists():
        sys.exit("error: vector index not found\n  run: build_skill_vectors.py --rebuild")
    client = chromadb.PersistentClient(path=str(VECTORS_DIR))
    try:
        collection = client.get_collection("skills")
    except ValueError:
        sys.exit("error: collection 'skills' not found\n  run: build_skill_vectors.py --rebuild")
    data = collection.get(include=["embeddings", "metadatas"])
    if not data["ids"]:
        sys.exit("error: collection is empty\n  run: build_skill_vectors.py --rebuild")

    chunks: dict[str, list[Vector]] = {}
    for meta, emb in zip(data["metadatas"], data["embeddings"], strict=True):
        name = skill_name_from_path(meta.get("path", ""))
        chunks.setdefault(name, []).append(emb)

    vectors: dict[str, Vector] = {}
    for name, embs in chunks.items():
        vec = np.mean(np.array(embs), axis=0)
        norm = np.linalg.norm(vec)
        vectors[name] = (vec / norm).tolist() if norm else vec.tolist()
    return vectors


def pairwise_scores(vectors: dict[str, Vector]) -> dict[str, float]:
    """All unordered pairs as 'a|b' -> cosine similarity."""
    scores: dict[str, float] = {}
    for a, b in combinations(sorted(vectors), 2):
        scores[f"{a}|{b}"] = float(np.dot(vectors[a], vectors[b]))
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
        suffix = " [accepted, edge not yet added]" if feedback.get(f"{a}|{b}") == "accept" else ""
        print(f"suggest_edges.py feedback {a} {b} accept  # {score:.3f}{suffix}")


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
            print(f"suggest_edges.py feedback {a} {b} reject  # {score:.3f} ({reason})")


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
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("suggest", help="missing-edge candidates")
    p.add_argument("skill", nargs="?", help="restrict to pairs involving this skill")
    p.add_argument("-k", type=int, default=10, help="max suggestions (default: 10)")
    p.add_argument("--threshold", type=float, default=0.5, help="min similarity (default: 0.5)")

    p = sub.add_parser("drift", help="score changes on existing edges vs last snapshot")
    p.add_argument("--drop", type=float, default=0.10, help="flag if score dropped by this much")
    p.add_argument("--floor", type=float, default=0.35, help="flag if score below this")

    sub.add_parser("snapshot", help="record current pairwise scores (run after build_skill_vectors.py --rebuild)")

    p = sub.add_parser("feedback", help="record human decision on a pair")
    p.add_argument("a", metavar="skill-a", help="first skill name")
    p.add_argument("b", metavar="skill-b", help="second skill name")
    p.add_argument("decision", choices=["accept", "reject"], help="accept or reject the edge")

    args = parser.parse_args()

    if args.cmd == "feedback":
        cmd_feedback(args.a, args.b, args.decision)
        return

    vectors = load_vectors()
    if args.cmd == "snapshot":
        cmd_snapshot(vectors)
    elif args.cmd == "suggest":
        cmd_suggest(vectors, load_edges(), args.skill, args.k, args.threshold)
    elif args.cmd == "drift":
        cmd_drift(vectors, load_edges(), args.drop, args.floor)


if __name__ == "__main__":
    main()
