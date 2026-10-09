"""Skill graph: structural check, reverse dependents lookup, dot emission.

Python port of skill-graph.sh; stdlib-only so the pre-commit gate runs under
any python3. Verdict strings match the bash original.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from .common import AGENTS_MD, CONTRACT_MD, SKILLS_DIR
from .common import (
    load_ranks,
    mentioned_in,
    rank_of,
    skill_edges,
    skill_exists,
    skill_files,
    skill_name,
)

OK_MESSAGE = "skill graph: connected (no dangling links, no orphans, handoffs acyclic, all skills terminate)"


def check(
    skills_dir: Path = SKILLS_DIR, agents_md: Path = AGENTS_MD, contract: Path = CONTRACT_MD
) -> int:
    fail = 0
    files = skill_files(skills_dir)
    names = [skill_name(f, skills_dir) for f in files]
    agents_text = agents_md.read_text(encoding="utf-8") if agents_md.exists() else ""

    inbound_links: set[str] = set()
    next_edges: list[tuple[str, str]] = []
    parsed = {}
    for path in files:
        src = skill_name(path, skills_dir)
        text = path.read_text(encoding="utf-8")
        links, nexts = skill_edges(text)
        parsed[src] = (links, nexts)
        for link in links:
            if not skill_exists(link, skills_dir):
                print(f"DANGLING: {src} -> [[{link}]]")
                fail = 1
            if link != src:
                inbound_links.add(link)
        for tgt in nexts:
            next_edges.append((src, tgt))

    for name in names:
        if name in inbound_links or mentioned_in(name, agents_text):
            continue
        if any(tgt == name for _, tgt in next_edges):
            continue
        print(f"ORPHAN: {name}")
        fail = 1

    ranks = load_ranks(contract)
    for src, (links, nexts) in parsed.items():
        if not nexts:
            print(f"NO-HANDOFF: {src} declares no next: verdict")
            fail = 1
            continue
        for tgt in nexts:
            if tgt == "done":
                continue
            rs = rank_of(src, ranks)
            if rs is None:
                print(f"UNRANKED: {src} (missing from rank table)")
                fail = 1
                continue
            rt = rank_of(tgt, ranks)
            if rt is None:
                print(f"UNRANKED: {tgt} (target of {src}, missing from rank table)")
                fail = 1
                continue
            if rt <= rs:
                print(f"RANK-VIOLATION: {src} (rank {rs}) -> {tgt} (rank {rt})")
                fail = 1

    if fail == 0:
        print(OK_MESSAGE)
    return fail


def dependents(target: str, skills_dir: Path = SKILLS_DIR, agents_md: Path = AGENTS_MD) -> int:
    found = False
    for path in skill_files(skills_dir):
        src = skill_name(path, skills_dir)
        if src == target:
            continue
        links, nexts = skill_edges(path.read_text(encoding="utf-8"))
        if target in links:
            print(f"LINK  {src} -> [[{target}]]")
            found = True
        if target in nexts:
            print(f"NEXT  {src} -> next: {target}")
            found = True
    if agents_md.exists():
        text = agents_md.read_text(encoding="utf-8")
        if mentioned_in(target, text):
            print(f"ROUTE AGENTS.md routing table mentions {target}")
            found = True
    if not found:
        print(f"no dependents: {target}")
    return 0


def emit_dot(skills_dir: Path = SKILLS_DIR) -> str:
    lines = [
        "digraph skills {",
        "  rankdir=LR;",
        '  node [shape=box, style=rounded, fontname="Helvetica"];',
        '  edge [color="#666666"];',
    ]
    for path in skill_files(skills_dir):
        name = skill_name(path, skills_dir)
        node_id = name.replace("/", "_")
        label = name.split("/")[-1]
        if "/" in name:
            lines.append(f'  "{node_id}" [label="{label}"];')
        else:
            lines.append(f'  "{node_id}" [label="{name}", style="rounded,bold"];')
        links, _ = skill_edges(path.read_text(encoding="utf-8"))
        for link in sorted(links):
            lines.append(f'  "{node_id}" -> "{link.replace("/", "_")}";')
    lines.append("}")
    return "\n".join(lines) + "\n"


def render(output: Path, skills_dir: Path = SKILLS_DIR) -> int:
    dot = shutil.which("dot")
    if dot is None:
        print("graphviz required: brew install graphviz", file=sys.stderr)
        return 1
    dot_file = output.with_suffix(".dot")
    dot_file.write_text(emit_dot(skills_dir), encoding="utf-8")
    fmt = output.suffix.lstrip(".") or "png"
    subprocess.run([dot, f"-T{fmt}", str(dot_file), "-o", str(output)], check=True)
    print(f"Generated: {output}")
    print(f"DOT source: {dot_file}")
    return 0
