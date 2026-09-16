#!/usr/bin/env python3
"""Query the semantic code index.

Usage:
    python query.py search "fetch package metadata"
    python query.py search "async http request" --type method
    python query.py list-classes
    python query.py list-methods [ClassName]
    python query.py show ClassName.method_name
    python query.py similar method_name
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("ChromaDB not installed. Install with: pip install chromadb")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent


def get_collection():
    """Get the code entities collection."""
    db_dir = SCRIPT_DIR / "chroma_db"
    if not db_dir.exists():
        print("Index not found. Run build_index.py first.")
        sys.exit(1)

    client = chromadb.PersistentClient(
        path=str(db_dir), settings=Settings(anonymized_telemetry=False)
    )
    return client.get_collection("code_entities")


def format_result(metadata: dict, document: str = None, show_code: bool = False) -> str:
    """Format a single result for display."""
    file_rel = Path(metadata["file"]).name
    location = f"{file_rel}:{metadata['line']}"

    if metadata["type"] == "method" and metadata.get("parent_class"):
        name = f"{metadata['parent_class']}.{metadata['name']}"
    else:
        name = metadata["name"]

    output = [
        f"\n{'=' * 60}",
        f"[{metadata['type'].upper()}] {name}",
        f"Location: {location}",
        f"Signature: {metadata['signature']}",
    ]

    if metadata.get("decorators"):
        output.append(f"Decorators: {metadata['decorators']}")

    if show_code and document:
        code_start = document.find("code: ")
        if code_start != -1:
            code = document[code_start + 6 :]
            if len(code) > 500:
                code = code[:500] + "\n... (truncated)"
            output.append(f"\n{code}")

    return "\n".join(output)


def search(
    query: str,
    entity_type: str | None = None,
    n_results: int = 5,
    show_code: bool = False,
):
    """Semantic search for code entities."""
    collection = get_collection()
    where_filter = {"type": entity_type} if entity_type else None

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_filter,
        include=["metadatas", "documents", "distances"],
    )

    if not results["ids"][0]:
        print(f"No results found for: {query}")
        return

    print(f"\nSearch: '{query}'\nFound {len(results['ids'][0])} results:\n")

    for i, (meta, doc, dist) in enumerate(
        zip(results["metadatas"][0], results["documents"][0], results["distances"][0])
    ):
        print(f"[{i + 1}] Relevance: {1 - dist:.2f}")
        print(format_result(meta, doc, show_code))


def list_classes():
    """List all classes in the index."""
    collection = get_collection()
    results = collection.get(where={"type": "class"}, include=["metadatas"])

    if not results["ids"]:
        print("No classes found.")
        return

    print(f"\nClasses ({len(results['ids'])}):\n")

    by_file: dict[str, list] = {}
    for meta in results["metadatas"]:
        file_name = Path(meta["file"]).name
        by_file.setdefault(file_name, []).append(meta)

    for file_name, classes in sorted(by_file.items()):
        print(f"\n{file_name}:")
        for cls in sorted(classes, key=lambda x: x["line"]):
            decorators = f" ({cls['decorators']})" if cls.get("decorators") else ""
            print(f"  {cls['name']}{decorators} (line {cls['line']})")


def list_methods(class_name: str | None = None):
    """List methods, optionally filtered by class."""
    collection = get_collection()

    if class_name:
        where_filter = {"$and": [{"type": "method"}, {"parent_class": class_name}]}
    else:
        where_filter = {"type": "method"}

    results = collection.get(where=where_filter, include=["metadatas"])

    if not results["ids"]:
        msg = (
            f"No methods found for class {class_name}"
            if class_name
            else "No methods found"
        )
        print(msg)
        return

    print(f"\nMethods ({len(results['ids'])}):")

    by_class: dict[str, list] = {}
    for meta in results["metadatas"]:
        parent = meta.get("parent_class") or "(module level)"
        by_class.setdefault(parent, []).append(meta)

    for cls_name, methods in sorted(by_class.items()):
        print(f"\n{cls_name}:")
        for method in sorted(methods, key=lambda x: x["line"]):
            sig = method["signature"].removeprefix("def ").removeprefix("async def ")
            file_name = Path(method["file"]).name
            print(f"  {sig}  [{file_name}:{method['line']}]")


def list_functions():
    """List all standalone functions."""
    collection = get_collection()
    results = collection.get(where={"type": "function"}, include=["metadatas"])

    if not results["ids"]:
        print("No standalone functions found.")
        return

    print(f"\nFunctions ({len(results['ids'])}):\n")

    by_file: dict[str, list] = {}
    for meta in results["metadatas"]:
        file_name = Path(meta["file"]).name
        by_file.setdefault(file_name, []).append(meta)

    for file_name, funcs in sorted(by_file.items()):
        print(f"\n{file_name}:")
        for func in sorted(funcs, key=lambda x: x["line"]):
            sig = func["signature"].removeprefix("def ").removeprefix("async def ")
            if func["signature"].startswith("async"):
                sig = "async " + sig
            print(f"  {sig}  (line {func['line']})")


def show(name: str):
    """Show details of a specific entity by name."""
    collection = get_collection()

    if "." in name:
        class_name, method_name = name.split(".", 1)
        where_filter = {"$and": [{"name": method_name}, {"parent_class": class_name}]}
    else:
        where_filter = {"name": name}

    results = collection.get(where=where_filter, include=["metadatas", "documents"])

    if not results["ids"]:
        search(name, n_results=3)
        return

    for meta, doc in zip(results["metadatas"], results["documents"]):
        print(format_result(meta, doc, show_code=True))


def similar(name: str, n_results: int = 5):
    """Find entities similar to a named one."""
    collection = get_collection()

    if "." in name:
        class_name, method_name = name.split(".", 1)
        where_filter = {"$and": [{"name": method_name}, {"parent_class": class_name}]}
    else:
        where_filter = {"name": name}

    target = collection.get(where=where_filter, include=["documents"])

    if not target["ids"]:
        print(f"Entity not found: {name}")
        return

    results = collection.query(
        query_texts=[target["documents"][0]],
        n_results=n_results + 1,
        include=["metadatas", "distances"],
    )

    print(f"\nEntities similar to '{name}':\n")

    count = 0
    for meta, dist in zip(results["metadatas"][0], results["distances"][0]):
        if meta["name"] == name.split(".")[-1]:
            continue
        if meta["type"] == "method" and meta.get("parent_class"):
            full_name = f"{meta['parent_class']}.{meta['name']}"
        else:
            full_name = meta["name"]
        file_name = Path(meta["file"]).name
        print(
            f"  {1 - dist:.2f}  {meta['type']:8}  {full_name:40}  [{file_name}:{meta['line']}]"
        )
        count += 1
        if count >= n_results:
            break


def stats():
    """Show index statistics."""
    stats_path = SCRIPT_DIR / "chroma_db" / "stats.json"

    if stats_path.exists():
        data = json.loads(stats_path.read_text())
        print("\nIndex Statistics:")
        print(f"  Files indexed: {data['files']}")
        print(f"  Classes: {data['classes']}")
        print(f"  Methods: {data['methods']}")
        print(f"  Functions: {data['functions']}")
        print(f"  Total entities: {data['total']}")
    else:
        collection = get_collection()
        print(f"\nTotal indexed entities: {collection.count()}")


def main():
    parser = argparse.ArgumentParser(description="Query the semantic code index")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_p = subparsers.add_parser("search", help="Semantic search for code")
    search_p.add_argument("query", help="Search query")
    search_p.add_argument("--type", "-t", choices=["class", "method", "function"])
    search_p.add_argument("--n-results", "-n", type=int, default=5)
    search_p.add_argument("--code", "-c", action="store_true", help="Show source code")

    subparsers.add_parser("list-classes", help="List all classes")

    methods_p = subparsers.add_parser("list-methods", help="List methods")
    methods_p.add_argument("class_name", nargs="?", help="Filter by class name")

    subparsers.add_parser("list-functions", help="List standalone functions")

    show_p = subparsers.add_parser("show", help="Show entity details")
    show_p.add_argument("name", help="Entity name (e.g., ClassName.method)")

    similar_p = subparsers.add_parser("similar", help="Find similar entities")
    similar_p.add_argument("name", help="Entity name to compare against")
    similar_p.add_argument("--n-results", "-n", type=int, default=5)

    subparsers.add_parser("stats", help="Show index statistics")

    args = parser.parse_args()

    match args.command:
        case "search":
            search(args.query, args.type, args.n_results, args.code)
        case "list-classes":
            list_classes()
        case "list-methods":
            list_methods(args.class_name)
        case "list-functions":
            list_functions()
        case "show":
            show(args.name)
        case "similar":
            similar(args.name, args.n_results)
        case "stats":
            stats()


if __name__ == "__main__":
    main()
