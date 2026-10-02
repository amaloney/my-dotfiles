"""Usage: python3 build_graph.py [research_dir] [--format html|json|dot] [-o out]

Builds a link graph from [[wiki-links]] in the research dir's markdown notes
and writes it as HTML (default, interactive), JSON, or DOT."""

import json
import re
import sys
from pathlib import Path

LINK = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")


def collect(root: Path) -> tuple[set[str], set[tuple[str, str]]]:
    nodes, edges = set(), set()
    for md in root.rglob("*.md"):
        src = md.stem
        nodes.add(src)
        for target in LINK.findall(md.read_text(encoding="utf-8")):
            edges.add((src, target.strip()))
    nodes.update(b for _, b in edges)
    return nodes, edges


def as_dot(nodes: set[str], edges: set[tuple[str, str]]) -> str:
    lines = ["digraph research {"]
    lines += [f'  "{n}";' for n in sorted(nodes)]
    lines += [f'  "{a}" -> "{b}";' for a, b in sorted(edges)]
    return "\n".join(lines + ["}"])


def as_html(nodes: set[str], edges: set[tuple[str, str]]) -> str:
    out = ["<!doctype html><meta charset=utf-8><title>Research graph</title>",
           "<h1>Research graph</h1>"]
    outlinks = {n: sorted(b for a, b in edges if a == n) for n in sorted(nodes)}
    for n in sorted(nodes):
        out.append(f'<details id="{n}"><summary>{n}</summary><ul>')
        out += [f'<li><a href="#{t}">{t}</a></li>' for t in outlinks[n]]
        out.append("</ul></details>")
    return "\n".join(out)


def main(argv: list[str]) -> None:
    root = Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("-") else Path("research")
    fmt = argv[argv.index("--format") + 1] if "--format" in argv else "html"
    out = Path(argv[argv.index("-o") + 1] if "-o" in argv else f"graph.{fmt}")
    nodes, edges = collect(root)
    data = {"nodes": sorted(nodes), "edges": sorted(map(list, edges))}
    text = {"json": json.dumps(data, indent=2), "dot": as_dot(nodes, edges)}.get(
        fmt, as_html(nodes, edges))
    out.write_text(text, encoding="utf-8")
    print(f"{len(nodes)} nodes, {len(edges)} edges -> {out}")


if __name__ == "__main__":
    main(sys.argv)
