"""llm-skills-network CLI: single entry point for skill graph + vector maintenance.

Subcommands:
  build --skill-vectors [--rebuild] [--if-stale]
  build --graph [--check | --dependents <skill> | [--output] <path>]
  edges --suggest [<skill>] [-k N] [--threshold F]
  edges --compute-drift [--drop F] [--floor F]
  edges --snapshot
  edges --feedback <a> <b> accept|reject
  edges --apply <a> <b>

Stdlib-only paths (graph check, feedback, apply) run under any python3;
chromadb/sentence-transformers are imported lazily only where needed.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm_skills_network import graph
from llm_skills_network.common import SKILLS_DIR, VECTORS_DIR, load_ranks, rank_of

DEBOUNCE_SECONDS = 600


def _suggest_edges():
    import suggest_edges

    return suggest_edges


def build_vectors(rebuild: bool) -> int:
    import build_skill_vectors

    return build_skill_vectors.build(rebuild=rebuild)


def build_vectors_if_stale() -> int:
    stamp = VECTORS_DIR / ".last_build"
    now = time.time()
    if stamp.exists():
        try:
            if now - float(stamp.read_text(encoding="utf-8").strip()) < DEBOUNCE_SECONDS:
                return 0
        except ValueError:
            pass
        newest = max((p.stat().st_mtime for p in SKILLS_DIR.glob("**/SKILL.md")), default=0)
        if newest <= stamp.stat().st_mtime:
            return 0
    try:
        import chromadb  # noqa: F401
        import sentence_transformers  # noqa: F401
    except ImportError:
        print("chromadb/sentence_transformers missing — skill vectors skipped", file=sys.stderr)
        return 0
    if build_vectors(rebuild=True) == 0:
        VECTORS_DIR.mkdir(parents=True, exist_ok=True)
        stamp.write_text(str(int(now)), encoding="utf-8")
        print("skill vectors rebuilt")
    else:
        print("skill vector rebuild failed", file=sys.stderr)
    return 0


def apply_edge(a: str, b: str) -> int:
    """Materialize an accepted edge into the source SKILL.md, rank-aware."""
    feedback_file = VECTORS_DIR / "edge_feedback.json"
    feedback = json.loads(feedback_file.read_text(encoding="utf-8")) if feedback_file.exists() else {}
    pair = "|".join(sorted((a, b)))
    if feedback.get(pair) != "accept":
        print(f"error: no recorded accept for {pair}; run: edges --feedback {a} {b} accept", file=sys.stderr)
        return 1
    source_md = SKILLS_DIR / a / "SKILL.md"
    if not source_md.exists():
        print(f"error: unknown skill '{a}'", file=sys.stderr)
        return 1
    if not (SKILLS_DIR / b / "SKILL.md").exists():
        print(f"error: unknown skill '{b}'", file=sys.stderr)
        return 1

    ranks = load_ranks()
    ra, rb = rank_of(a, ranks), rank_of(b, ranks)
    if ra is None or rb is None:
        print(f"error: rank unknown ({a}={ra}, {b}={rb}); add edge manually", file=sys.stderr)
        return 1

    text = source_md.read_text(encoding="utf-8")
    if rb > ra:
        addition = f"\nHandoff: also `next: {b}`.\n"
        kind = f"handoff next: {b} (rank {ra} -> {rb})"
    else:
        addition = f"\nSee [[{b}]].\n"
        kind = f"reference [[{b}]] (rank {ra} -> {rb}; backward/equal ranks cannot hand off)"

    source_md.write_text(text.rstrip("\n") + "\n" + addition, encoding="utf-8")
    if graph.check() != 0:
        source_md.write_text(text, encoding="utf-8")
        print(f"error: graph check failed after edit; reverted {source_md}", file=sys.stderr)
        return 1
    print(f"applied: {a} -> {kind}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="llm-skills-network",
        description="Single CLI for the skill network: graph structure, vectors, edges.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="build graph artifacts or skill vectors")
    p_build.add_argument("--skill-vectors", action="store_true", help="(re)build the vector index")
    p_build.add_argument("--rebuild", action="store_true", help="delete and rebuild the index")
    p_build.add_argument(
        "--if-stale",
        action="store_true",
        help="rebuild only if a SKILL.md changed; debounced; never fails",
    )
    p_build.add_argument("--graph", action="store_true", help="graph operations (skill-graph.sh port)")
    p_build.add_argument("--check", action="store_true", help="structural gate; exit 1 on problems")
    p_build.add_argument("--dependents", metavar="SKILL", help="who points at SKILL")
    p_build.add_argument("--output", metavar="PATH", help="render output path (png/svg)")
    p_build.add_argument("output_pos", nargs="?", help=argparse.SUPPRESS)

    p_edges = sub.add_parser("edges", help="edge suggestions, drift, snapshots, feedback")
    group = p_edges.add_mutually_exclusive_group(required=True)
    group.add_argument("--suggest", nargs="?", const="", metavar="SKILL", help="missing-edge candidates")
    group.add_argument("--compute-drift", action="store_true", help="score changes on existing edges")
    group.add_argument("--snapshot", action="store_true", help="record current pairwise scores")
    group.add_argument("--feedback", nargs=3, metavar=("A", "B", "DECISION"), help="accept|reject a pair")
    group.add_argument("--apply", nargs=2, metavar=("A", "B"), help="materialize an accepted edge")
    p_edges.add_argument("-k", type=int, default=10, help="max suggestions (default: 10)")
    p_edges.add_argument("--threshold", type=float, default=0.5, help="min similarity (default: 0.5)")
    p_edges.add_argument("--drop", type=float, default=0.10, help="drift drop threshold")
    p_edges.add_argument("--floor", type=float, default=0.35, help="weak edge floor")

    args = parser.parse_args(argv)

    if args.cmd == "build":
        if args.skill_vectors:
            if args.if_stale:
                return build_vectors_if_stale()
            return build_vectors(rebuild=args.rebuild)
        if args.graph:
            if args.check:
                return graph.check()
            if args.dependents:
                return graph.dependents(args.dependents)
            output_arg = args.output or args.output_pos
            output = Path(output_arg) if output_arg else SKILLS_DIR.parent / "skill-graph.png"
            return graph.render(output)
        parser.error("build: pass --skill-vectors or --graph")

    if args.cmd == "edges":
        if args.feedback:
            a, b, decision = args.feedback
            if decision not in ("accept", "reject"):
                parser.error("edges --feedback: DECISION must be accept or reject")
            _suggest_edges().cmd_feedback(a, b, decision)
            return 0
        if args.apply:
            return apply_edge(args.apply[0], args.apply[1])
        se = _suggest_edges()
        vectors = se.load_vectors()
        if args.snapshot:
            se.cmd_snapshot(vectors)
            return 0
        if args.suggest is not None:
            skill = args.suggest or None
            se.cmd_suggest(vectors, se.load_edges(), skill, args.k, args.threshold)
            return 0
        if args.compute_drift:
            se.cmd_drift(vectors, se.load_edges(), args.drop, args.floor)
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
