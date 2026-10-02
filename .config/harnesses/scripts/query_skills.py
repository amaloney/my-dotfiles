#!/usr/bin/env python3
"""Query skill vector index with distance scores.

Usage:
    python ~/.claude/scripts/query_skills.py "write a batch script"
    python ~/.claude/scripts/query_skills.py "conda installer" -k 3
    python ~/.claude/scripts/query_skills.py --stats
    python ~/.claude/scripts/query_skills.py --list

Output shows cosine similarity scores (0-1, higher = closer match).
"""

import argparse
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


def get_collection():
    """Get the skills collection."""
    vectors_dir = Path.home() / ".claude" / "vectors"

    if not vectors_dir.exists():
        print("Vector index not found. Run:", file=sys.stderr)
        print("  python ~/.claude/scripts/build_skill_vectors.py", file=sys.stderr)
        sys.exit(1)

    client = chromadb.PersistentClient(path=str(vectors_dir))

    try:
        return client.get_collection("skills")
    except ValueError:
        print(
            "Collection 'skills' not found. Run build_skill_vectors.py", file=sys.stderr
        )
        sys.exit(1)


def query(text: str, k: int = 5, threshold: float = 0.0):
    """Query the vector index and return results with scores."""
    collection = get_collection()

    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_embedding = model.encode(text).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    if not results["ids"][0]:
        print("No results found.")
        return []

    print(f'\nQuery: "{text}"')
    print("-" * 60)

    matches = []
    for doc_id, doc, meta, dist in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        score = 1 - dist  # Cosine distance to similarity

        if score < threshold:
            continue

        matches.append(
            {
                "name": meta.get("name", doc_id),
                "score": score,
                "description": meta.get("description", ""),
                "path": meta.get("path", ""),
                "triggers": meta.get("triggers", ""),
            }
        )

        # Truncate for display
        doc_preview = doc[:200].replace("\n", " ")
        if len(doc) > 200:
            doc_preview += "..."

        print(f"\n{meta.get('name', doc_id)}")
        print(f"  Score: {score:.3f}")
        print(f"  Desc: {meta.get('description', 'N/A')}")
        if meta.get("triggers"):
            print(f"  Triggers: {meta['triggers'][:60]}...")
        print(f"  Preview: {doc_preview}")

    print("-" * 60)

    # Recommendation
    if matches:
        best = matches[0]
        if best["score"] >= 0.7:
            print(f"\nRECOMMENDATION: Load '{best['name']}' (high confidence)")
        elif best["score"] >= 0.4:
            print(f"\nSUGGESTION: Consider '{best['name']}' (moderate match)")
        else:
            print("\nNO STRONG MATCH: Ask user for docs/reference")
    else:
        print("\nNO MATCH: Ask user for authoritative source")

    return matches


def show_stats():
    """Show index statistics."""
    collection = get_collection()

    total = collection.count()
    all_docs = collection.get(include=["metadatas"])

    skills = {}
    for meta in all_docs["metadatas"]:
        name = meta.get("name", "unknown")
        skills[name] = skills.get(name, 0) + 1

    print("\nSkill Vector Index Statistics")
    print("=" * 40)
    print(f"Total chunks: {total}")
    print(f"Unique skills: {len(skills)}")
    print()
    print("By skill (chunks):")
    for name, count in sorted(skills.items()):
        print(f"  {name}: {count}")


def list_skills():
    """List all indexed skills."""
    collection = get_collection()
    all_docs = collection.get(include=["metadatas"])

    skills = {}
    for meta in all_docs["metadatas"]:
        name = meta.get("name", "unknown")
        if name not in skills:
            skills[name] = {
                "description": meta.get("description", ""),
                "path": meta.get("path", ""),
            }

    print("\nIndexed Skills")
    print("=" * 60)
    for name, info in sorted(skills.items()):
        print(f"\n{name}")
        print(
            f"  {info['description'][:70]}..."
            if len(info["description"]) > 70
            else f"  {info['description']}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Query skill vector index with distance scores",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "write a batch script"
  %(prog)s "conda custom installer" -k 3
  %(prog)s "frustrated customer QA" --threshold 0.4
  %(prog)s --stats
  %(prog)s --list
        """,
    )

    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument(
        "-k", type=int, default=5, help="Number of results (default: 5)"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.0, help="Minimum similarity score (0-1)"
    )
    parser.add_argument("--stats", action="store_true", help="Show index statistics")
    parser.add_argument("--list", action="store_true", help="List all indexed skills")

    args = parser.parse_args()

    if args.stats:
        show_stats()
    elif args.list:
        list_skills()
    elif args.query:
        query(args.query, args.k, args.threshold)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
