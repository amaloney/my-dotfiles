#!/usr/bin/env python3
"""Skill edge suggestions, drift detection, and human feedback.

Reads skill-level embeddings from the vector store (mean of each skill's chunk
embeddings) and the existing edge set from SKILL.md files ([[links]] + next:
verdicts, same rules as skill-graph.sh).

Usage:
    python suggest_edges.py suggest [skill] [-k 5] [--threshold 0.5]
    python suggest_edges.py drift [--drop 0.10] [--floor 0.35]
    python suggest_edges.py snapshot
    python suggest_edges.py feedback <skill-a> <skill-b> accept|reject

State (both gitignored, under ~/.config/harnesses/vectors/):
    edge_scores.json    timestamped snapshots of pairwise scores (drift history)
    edge_feedback.json  human accept/reject decisions per skill pair
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import chromadb

SKILLS_DIR = Path.home() / ".config" / "harnesses" / "skills"
VECTORS_DIR = Path.home() / ".config" / "harnesses" / "vectors"
SCORES_FILE = VECTORS_DIR / "edge_scores.json"
FEEDBACK_FILE = VECTORS_DIR / "edge_feedback.json"
MAX_SNAPSHOTS = 10

LINK_RE = re.compile(r"\[\[([a-z][a-z0-9/_-]*)\]\]")
NEXT_RE = re.compile(r"next: `?(?:\[\[)?([a-z0-9/_-]+)")


def skill_name_from_path(path: str) -> str:
    """Dir name relative to skills/, e.g. python/recon."""
    return str(Path(path).parent.relative_to(SKILLS_DIR))


def load_edges() -> set[tuple[str, str]]:
    """Existing edges as unordered pairs (a, b) with a < b."""
    edges = set()
    for skill_path in SKILLS_DIR.glob("**/SKILL.md"):
        src = str(skill_path.parent.relative_to(SKILLS_DIR))
        text = skill_path.read_text()
        targets = set(LINK_RE.findall(text)) | set(NEXT_RE.findall(text))
        for tgt in targets:
            if tgt != "done" and tgt != src:
                edges.add(tuple(sorted((src, tgt))))
    return edges


def load_vectors() -> dict[str, list[float]]:
    """Skill-level embedding = mean of its chunk embeddings, L2-normalized."""
    if not VECTORS_DIR.exists():
        sys.exit("Vector index not found. Run build_skill_vectors.py --rebuild")
    client = chromadb.PersistentClient(path=str(VECTORS_DIR))
    try:
        collection = client.get_collection("skills")
    except ValueError:
        sys.exit("Collection 'skills' not found. Run build_skill_vectors.py --rebuild")
    data = collection.get(include=["embeddings", "metadatas"])
    if not data["ids"]:
        sys.exit("Collection is empty. Run build_skill_vectors.py --rebuild")

    import numpy as np

    chunks: dict[str, list[list[float]]] = {}
    for meta, emb in zip(data["metadatas"], data["embeddings"]):
        name = skill_name_from_path(meta.get("path", ""))
        chunks.setdefault(name, []).append(emb)

    vectors = {}
    for name, embs in chunks.items():
        vec = np.mean(np.array(embs), axis=0)
        norm = np.linalg.norm(vec)
        vectors[name] = (vec / norm).tolist() if norm else vec.tolist()
    return vectors


def pairwise_scores(vectors: dict[str, list[float]]) -> dict[str, float]:
    """All unordered pairs as 'a|b' -> cosine similarity."""
    import numpy as np

    scores = {}
    for a, b in combinations(sorted(vectors), 2):
        scores[f"{a}|{b}"] = float(np.dot(vectors[a], vectors[b]))
    return scores


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def cmd_snapshot(vectors) -> None:
    scores = pairwise_scores(vectors)
    history = load_json(SCORES_FILE, {"snapshots": []})
    history["snapshots"].append(
        {"ts": datetime.now(timezone.utc).isoformat(), "scores": scores}
    )
    history["snapshots"] = history["snapshots"][-MAX_SNAPSHOTS:]
    SCORES_FILE.write_text(json.dumps(history, indent=1))
    print(f"snapshot: {len(scores)} pairs recorded ({len(history['snapshots'])} kept)")


def cmd_suggest(vectors, edges, skill, k, threshold) -> None:
    scores = pairwise_scores(vectors)
    feedback = load_json(FEEDBACK_FILE, {})
    rejected = {tuple(k.split("|")) for k, v in feedback.items() if v == "reject"}

    candidates = []
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
    print(f"missing-edge candidates (threshold {threshold}):\n")
    for score, a, b in candidates[:k]:
        pending = ""
        if feedback.get(f"{a}|{b}") == "accept":
            pending = "  [accepted, edge not yet added]"
        print(f"  {score:.3f}  {a} <-> {b}{pending}")
    print("\nrecord a decision: suggest_edges.py feedback <a> <b> accept|reject")


def cmd_drift(vectors, edges, drop, floor) -> None:
    history = load_json(SCORES_FILE, {"snapshots": []})
    if len(history["snapshots"]) < 2:
        sys.exit("need 2 snapshots to measure drift. Rebuild the index after editing skills.")
    previous = history["snapshots"][-2]["scores"]
    current = history["snapshots"][-1]["scores"]

    flagged = 0
    print(f"edge drift (drop >= {drop} or score < {floor})")
    print(f"  {history['snapshots'][-2]['ts']} -> {history['snapshots'][-1]['ts']}\n")
    for a, b in sorted(edges):
        pair = f"{a}|{b}"
        if pair not in previous or pair not in current:
            continue
        delta = current[pair] - previous[pair]
        if delta <= -drop:
            print(f"  DRIFT {previous[pair]:.3f} -> {current[pair]:.3f}  ({delta:+.3f})  {a} -> {b}")
            flagged += 1
        elif current[pair] < floor:
            print(f"  WEAK  {current[pair]:.3f}  (below floor)  {a} -> {b}")
            flagged += 1
    if not flagged:
        print("  no drift on existing edges")


def cmd_feedback(a, b, decision) -> None:
    pair = "|".join(sorted((a, b)))
    feedback = load_json(FEEDBACK_FILE, {})
    feedback[pair] = decision
    FEEDBACK_FILE.write_text(json.dumps(feedback, indent=1, sort_keys=True))
    print(f"recorded: {pair} -> {decision}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("suggest", help="missing-edge candidates")
    p.add_argument("skill", nargs="?", help="restrict to pairs involving this skill")
    p.add_argument("-k", type=int, default=10)
    p.add_argument("--threshold", type=float, default=0.5)

    p = sub.add_parser("drift", help="score changes on existing edges vs last snapshot")
    p.add_argument("--drop", type=float, default=0.10)
    p.add_argument("--floor", type=float, default=0.35)

    sub.add_parser("snapshot", help="record current pairwise scores (run after --rebuild)")

    p = sub.add_parser("feedback", help="record human decision on a pair")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("decision", choices=["accept", "reject"])

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
