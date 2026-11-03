#!/usr/bin/env python3
"""Insert docstring skeletons from vim-doge-helper into functions that have none.

The helper (https://github.com/kkoomen/vim-doge/tree/master/helper) prints JSON:
    {"docblock": ["...", "..."], "line": N}
It never edits the file; this module does the insertion. Placeholders are left
for the agent to fill, and the todo rule in ast_rules.py fails until they're gone.
"""

import ast
import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

DOGE_DOC_NAME = os.environ.get("STYLE_GATES_DOGE_DOC", "google")
DOGE_TIMEOUT_SECONDS = 10
PLACEHOLDER = "[TODO:"


def find_helper() -> str | None:
    """Locate vim-doge-helper in PATH or common install locations."""
    if helper := shutil.which("vim-doge-helper"):
        return helper
    candidates = [Path.home() / ".cargo/bin/vim-doge-helper", Path("/usr/local/bin/vim-doge-helper")]
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def needs_docblock(tree: ast.Module) -> list[ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef]:
    """Module-level and class-level defs without a docstring (nested functions are skipped)."""
    candidates = []

    def visit(body: list[ast.stmt]) -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                is_dunder = node.name.startswith("__") and node.name.endswith("__")
                same_line_body = node.body[0].lineno == node.lineno
                if not (is_dunder or same_line_body or ast.get_docstring(node) is not None):
                    candidates.append(node)
                if isinstance(node, ast.ClassDef):
                    visit(node.body)

    visit(tree.body)
    return candidates


def request_docblock(helper: str, path: Path, line: int) -> list[str] | None:
    command = [helper, "--filepath", str(path), "--parser", "python", "--doc-name", DOGE_DOC_NAME, "--line", str(line)]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=DOGE_TIMEOUT_SECONDS)
        docblock = json.loads(result.stdout).get("docblock") if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired, ValueError, AttributeError):
        return None
    return docblock if isinstance(docblock, list) and docblock else None


def below_signature(lines: list[str], node: ast.stmt) -> int:
    """Index of the line right after the signature, above any leading comments or blank lines."""
    index = node.body[0].lineno - 1
    while index > node.lineno and (not lines[index - 1].strip() or lines[index - 1].lstrip().startswith("#")):
        index -= 1
    return index


def fill_docblocks(path: Path, helper: str) -> int:
    """Insert skeletons in place. Returns how many were inserted."""
    try:
        source = path.read_text()
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return 0
    lines = source.splitlines(keepends=True)
    insertions: list[tuple[int, list[str]]] = []
    for node in needs_docblock(tree):
        docblock = request_docblock(helper, path, node.lineno)
        if not docblock:
            continue
        first_statement = node.body[0]
        indent = lines[first_statement.lineno - 1][: first_statement.col_offset]
        block = textwrap.indent(textwrap.dedent("\n".join(docblock)), indent).rstrip() + "\n"
        insertions.append((below_signature(lines, node), block.splitlines(keepends=True)))

    for index, block_lines in sorted(insertions, reverse=True):
        lines[index:index] = block_lines
    if insertions:
        path.write_text("".join(lines))
    return len(insertions)


def main() -> int:
    """CLI entry point: docblocks.py <file.py> [file2.py ...]"""
    helper = find_helper()
    if not helper:
        print("vim-doge-helper not found", file=sys.stderr)
        return 1
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.py> [file2.py ...]", file=sys.stderr)
        return 1
    total = 0
    for arg in sys.argv[1:]:
        path = Path(arg)
        if path.suffix == ".py" and path.is_file():
            count = fill_docblocks(path, helper)
            if count:
                print(f"{path}: inserted {count} docstring(s)")
                total += count
    return 0 if total >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
