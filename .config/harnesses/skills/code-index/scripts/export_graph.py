#!/usr/bin/env python3
"""Export the code knowledge graph as JSON and a self-contained HTML explorer."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
TEMPLATE_PATH = SCRIPT_DIR / "viz_template.html"


def relative_path(file_path: str, root: Path) -> str:
    try:
        return str(Path(file_path).relative_to(root))
    except ValueError:
        return file_path


def module_name(path: str) -> str:
    dotted = path.removeprefix("src/").removesuffix(".py").replace("/", ".")
    return dotted.removesuffix(".__init__")


def group_of(path: str) -> str:
    parts = path.split("/")
    return "/".join(parts[:2]) if len(parts) > 2 else parts[0]


def resolve_import(target: str, module_to_file: dict[str, str]) -> str | None:
    parts = target.split(".")
    for end in range(len(parts), 0, -1):
        path = module_to_file.get(".".join(parts[:end]))
        if path:
            return path
    return None


def add_edge(edges: dict[tuple[str, str, str], int], source: str, target: str, kind: str) -> None:
    key = (source, target, kind)
    edges[key] = edges.get(key, 0) + 1


def to_edge_list(edges: dict[tuple[str, str, str], int]) -> list[dict]:
    return [
        {"source": source, "target": target, "kind": kind, "weight": weight}
        for (source, target, kind), weight in sorted(edges.items())
    ]


def build_graph(conn: sqlite3.Connection, root: Path) -> dict:
    entities = [
        dict(row)
        for row in conn.execute(
            "SELECT id, name, entity_type, file_path, line_start, line_end, signature FROM current_entities"
        )
    ]
    relations = [
        dict(row)
        for row in conn.execute(
            "SELECT source_id, target_id, target_name, rel_type FROM current_relations "
            "WHERE rel_type IN ('calls', 'inherits', 'imports')"
        )
    ]

    for entity in entities:
        entity["path"] = relative_path(entity["file_path"], root)
    entity_path = {entity["id"]: entity["path"] for entity in entities}
    module_to_file = {module_name(path): path for path in set(entity_path.values())}

    module_nodes: dict[str, dict] = {}
    for entity in entities:
        node = module_nodes.setdefault(
            entity["path"],
            {
                "id": entity["path"],
                "kind": "module",
                "label": Path(entity["path"]).name,
                "path": entity["path"],
                "group": group_of(entity["path"]),
                "objects": 0,
                "loc": 0,
            },
        )
        node["objects"] += 1
        node["loc"] = max(node["loc"], entity["line_end"] or entity["line_start"])

    module_edges: dict[tuple[str, str, str], int] = {}
    object_edges: dict[tuple[str, str, str], int] = {}
    objects_used_in: dict[str, set[str]] = {}
    for relation in relations:
        source_path = entity_path.get(relation["source_id"])
        if source_path is None:
            continue
        if relation["rel_type"] == "imports":
            target_path = resolve_import(relation["target_name"], module_to_file)
            if target_path and target_path != source_path:
                add_edge(module_edges, source_path, target_path, "imports")
            continue
        if relation["target_id"] not in entity_path:
            continue
        target_path = entity_path[relation["target_id"]]
        kind = relation["rel_type"]
        if target_path != source_path:
            add_edge(module_edges, source_path, target_path, kind)
        add_edge(object_edges, relation["source_id"], relation["target_id"], kind)
        objects_used_in.setdefault(relation["target_id"], set()).add(source_path)

    object_nodes = [
        {
            "id": entity["id"],
            "kind": entity["entity_type"],
            "label": entity["name"],
            "path": entity["path"],
            "line": entity["line_start"],
            "signature": entity["signature"] or "",
            "group": group_of(entity["path"]),
        }
        for entity in entities
    ]
    module_edge_list = to_edge_list(module_edges)
    object_edge_list = to_edge_list(object_edges)

    hyperedges = []
    for entity in entities:
        used_in = sorted(objects_used_in.get(entity["id"], set()) - {entity["path"]})
        hyperedges.append(
            {
                "id": entity["id"],
                "label": entity["name"],
                "kind": entity["entity_type"],
                "defined_in": entity["path"],
                "used_in": used_in,
                "modules": [entity["path"], *used_in],
            }
        )

    return {
        "root": str(root),
        "module": {"nodes": sorted(module_nodes.values(), key=lambda node: node["id"]), "edges": module_edge_list},
        "objects": {"nodes": object_nodes, "edges": object_edge_list},
        "hyperedges": hyperedges,
        "stats": {
            "modules": len(module_nodes),
            "objects": len(object_nodes),
            "module_edges": len(module_edge_list),
            "object_edges": len(object_edge_list),
            "hyperedges": len(hyperedges),
        },
    }


def render_html(graph: dict, template: str) -> str:
    payload = json.dumps(graph).replace("</", "<\\/")
    html, replacements = re.subn(r"/\*__GRAPH_DATA__\*/\s*null", lambda _: payload, template)
    if replacements != 1:
        raise ValueError(f"Expected one graph-data placeholder, found {replacements}")
    return html


def write_outputs(graph: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "graph.json").write_text(json.dumps(graph, indent=2))
    (out_dir / "index.html").write_text(render_html(graph, TEMPLATE_PATH.read_text()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Export code graph for humans and tools")
    parser.add_argument("--db-dir", type=Path, default=SCRIPT_DIR, help="Directory containing code_graph.db")
    parser.add_argument("--out", type=Path, default=None, help="Output directory (default: <db-dir>/viz)")
    args = parser.parse_args()

    db_dir = args.db_dir.resolve()
    out_dir = args.out or db_dir / "viz"
    db_path = db_dir / "code_graph.db"
    if not db_path.exists():
        raise SystemExit(f"{db_path} not found; build the index with build_index_temporal.py first")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        graph = build_graph(conn, db_dir.parent.parent)
    finally:
        conn.close()

    write_outputs(graph, out_dir)
    stats = graph["stats"]
    print(
        f"Exported {stats['modules']} modules, {stats['objects']} objects, "
        f"{stats['module_edges']} module edges, {stats['object_edges']} object edges, "
        f"{stats['hyperedges']} hyperedges to {out_dir}"
    )


if __name__ == "__main__":
    main()
