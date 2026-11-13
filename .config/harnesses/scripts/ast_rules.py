#!/usr/bin/env python3
"""Single-pass AST rules for style preferences that ruff and pyrefly don't cover.

Rules:
  naming     cryptic / single-letter names at binding sites (naming_check.py)
  private    underscore-prefixed functions and methods
  wrapper    one-line functions that only `return <expr>`
  comment    comments that restate the code they sit on
  docstring  one-line docstrings that restate the function or class name
  todo       docstrings that still contain vim-doge placeholders
  reuse      new functions that look like existing ones in the code index
"""

from __future__ import annotations

import ast
import difflib
import io
import json
import re
import subprocess
import tokenize
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from docblocks import PLACEHOLDER  # pyrefly: ignore[missing-import]
from naming_check import findings as naming_findings  # pyrefly: ignore[missing-import]
from naming_check import is_cryptic  # pyrefly: ignore[missing-import]

SUPPRESS_MARKERS = ("# style:allow", "# naming:allow")
SKIP_COMMENT = re.compile(r"noqa|type:|pyrefly|style:allow|naming:allow|todo|fixme|pragma|fmt:|-\*-", re.IGNORECASE)
WORD = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+")
MAX_REDUNDANT_COMMENT_WORDS = 12
REUSE_MIN_SCORE = 0.6
REUSE_MAX_CANDIDATES = 3


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    rule: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: [{self.rule}] {self.message}"


def stem(word: str) -> str:
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def words(text: str) -> set[str]:  # style:allow names a concept used 7x
    """Lowercased, crudely stemmed words from prose or snake/camel identifiers."""
    return {stem(match.lower()) for match in WORD.findall(text)}


FILLER_WORDS = words(
    "a an the this that these those of to for in on over through each every all and or "
    "with from by as is are be it its into then new loop iterate check call set get return "
    "create initialize init increment update add append function method helper variable value "
    "build make compute calculate store save define"
)


def naming_rule(path: Path, tree: ast.AST) -> list[Finding]:
    results, seen = [], set()
    for lineno, column, site, name, hint in sorted(naming_findings(tree)):
        if is_cryptic(name) and (lineno, column) not in seen:
            seen.add((lineno, column))
            tip = f" -> try `{hint}`" if hint and hint != name else ""
            results.append(Finding(path, lineno, "naming", f"[{site}] `{name}` is cryptic{tip}"))
    return results


def functions(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:  # style:allow
    return [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def is_dunder(name: str) -> bool:  # style:allow
    return name.startswith("__") and name.endswith("__")


def private_rule(path: Path, tree: ast.AST) -> list[Finding]:  # style:allow
    return [
        Finding(path, function.lineno, "private", f"`{function.name}` is underscore-prefixed; give it a public name")
        for function in functions(tree)
        if function.name.startswith("_") and function.name != "_" and not is_dunder(function.name)
    ]


def call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def wrapper_rule(path: Path, tree: ast.AST) -> list[Finding]:
    call_counts = Counter(call_name(node) for node in ast.walk(tree) if isinstance(node, ast.Call))
    results = []
    for function in functions(tree):
        if function.decorator_list or is_dunder(function.name):
            continue
        body = function.body[1:] if ast.get_docstring(function) is not None else function.body
        uses = call_counts[function.name]
        if uses and len(body) == 1 and isinstance(body[0], ast.Return) and body[0].value is not None:
            expression = ast.unparse(body[0].value)
            if len(expression) > 60:
                expression = expression[:57] + "..."
            results.append(
                Finding(
                    path,
                    function.lineno,
                    "wrapper",
                    f"`{function.name}` is a one-line wrapper (`return {expression}`), called {uses}x "
                    "in this file; inline it at the call site",
                )
            )
    return results


def next_code_line(lines: list[str], row: int) -> str:
    for line in lines[row:]:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return line
    return ""


def header_block_end(lines: list[str]) -> int:
    """Return the 1-indexed line number where the file header block ends.

    A header block is a contiguous run of comment/blank lines at the top of the file,
    optionally preceded by a shebang or encoding declaration. Returns 0 if no header.
    """
    if not lines:
        return 0
    start = 0
    first = lines[0].strip()
    if first.startswith("#!") or first.startswith("# -*-") or first.startswith("# coding"):
        start = 1
    end = start
    for i, line in enumerate(lines[start:], start=start):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            end = i + 1
        else:
            break
    return end if end > start else 0


def comment_rule(path: Path, source: str, lines: list[str]) -> list[Finding]:
    results = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, SyntaxError):
        return results
    header_end = header_block_end(lines)
    for token in tokens:
        if token.type != tokenize.COMMENT:
            continue
        row, column = token.start
        if row <= header_end:
            continue
        text = token.string.lstrip("#").strip()
        if not text or text.startswith("!") or SKIP_COMMENT.search(text):
            continue
        if len(text.split()) > MAX_REDUNDANT_COMMENT_WORDS:
            continue
        own_line = lines[row - 1]
        code = next_code_line(lines, row) if own_line.strip().startswith("#") else own_line[:column]
        meaningful = words(text) - FILLER_WORDS
        if code and meaningful <= words(code):
            results.append(
                Finding(path, row, "comment", f"`# {text}` restates the code; delete it or explain why instead of what")
            )
    return results


def docstring_rule(path: Path, tree: ast.AST) -> list[Finding]:
    results = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        docstring = ast.get_docstring(node)
        if docstring and PLACEHOLDER in docstring:
            name = getattr(node, "name", "module")
            results.append(
                Finding(
                    path,
                    getattr(node, "lineno", 1),
                    "todo",
                    f"docstring of `{name}` still has `{PLACEHOLDER}...]` placeholders; "
                    "replace each with a real description",
                )
            )
            continue
        if isinstance(node, ast.Module) or not docstring or "\n" in docstring.strip():
            continue
        if words(docstring) - FILLER_WORDS <= words(node.name):
            results.append(
                Finding(
                    path,
                    node.lineno,
                    "docstring",
                    f'docstring of `{node.name}` restates its name ("{docstring.strip()}"); '
                    "describe behavior, inputs, or edge cases instead",
                )
            )
    return results


def load_index(index_path: Path) -> list[tuple[str, str]]:
    """Return (function name, location) pairs.

    Accepts JSON (`[{"name", "path", "line"}]` or `{"name": "path"}`) or a ctags file.
    """
    text = index_path.read_text()
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    entries: list[tuple[str, str]] = []
    if isinstance(data, dict):
        entries = [(str(name), str(location)) for name, location in data.items()]
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "name" in item:
                location = f"{item.get('path', '?')}:{item.get('line', '')}".rstrip(":")
                entries.append((str(item["name"]), location))
    else:
        for line in text.splitlines():
            if line.startswith("!") or "\t" not in line:
                continue
            name, location, *_ = line.split("\t")
            entries.append((name, location))
    return [(name.rsplit(".", 1)[-1], location) for name, location in entries]


def defined_names(tree: ast.AST) -> set[str]:  # style:allow
    return {function.name for function in functions(tree)}


def baseline_names(path: Path) -> set[str]:
    """Function names in the last committed version of the file (empty if new or no git)."""
    try:
        result = subprocess.run(
            ["git", "-C", str(path.parent), "show", f"HEAD:./{path.name}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return set()
    if result.returncode != 0:
        return set()
    try:
        return defined_names(ast.parse(result.stdout))
    except SyntaxError:
        return set()


def similarity(new_name: str, existing_name: str) -> float:
    new_words, existing_words = words(new_name), words(existing_name)
    shared = new_words & existing_words
    jaccard = len(shared) / len(new_words | existing_words) if new_words | existing_words else 0.0
    ratio = difflib.SequenceMatcher(None, new_name, existing_name).ratio()
    if len(shared) < 2 and ratio < 0.85:
        return 0.0
    return max(jaccard, ratio)


def same_file(path: Path, location: str) -> bool:
    location_file = location.split(":", 1)[0].removeprefix("./")
    return path.resolve().as_posix().endswith(location_file)


def reuse_rule(path: Path, tree: ast.AST, index: list[tuple[str, str]]) -> list[Finding]:
    new_names = defined_names(tree) - baseline_names(path)
    line_of = {function.name: function.lineno for function in functions(tree)}
    results = []
    for new_name in sorted(new_names):
        if is_dunder(new_name):
            continue
        scored = sorted(
            (
                (similarity(new_name, name), name, location)
                for name, location in index
                if not (name == new_name and same_file(path, location))
            ),
            reverse=True,
        )
        candidates = [
            f"`{name}` ({location})"
            for score, name, location in scored[:REUSE_MAX_CANDIDATES]
            if score >= REUSE_MIN_SCORE
        ]
        if candidates:
            results.append(
                Finding(
                    path,
                    line_of[new_name],
                    "reuse",
                    f"new function `{new_name}` resembles {', '.join(candidates)}; "
                    "extend the existing function instead of adding a new one",
                )
            )
    return results


def suppressed(lines: list[str], line: int) -> bool:  # style:allow
    return 0 < line <= len(lines) and any(marker in lines[line - 1] for marker in SUPPRESS_MARKERS)


def check_file(path: Path, index: list[tuple[str, str]] | None = None) -> list[Finding]:
    """Parse once, run every rule. Pass `index` to include the reuse rule."""
    try:
        source = path.read_text()
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []
    lines = source.splitlines()
    results = [
        *naming_rule(path, tree),
        *private_rule(path, tree),
        *wrapper_rule(path, tree),
        *comment_rule(path, source, lines),
        *docstring_rule(path, tree),
    ]
    if index:
        results += reuse_rule(path, tree, index)
    return sorted(
        (finding for finding in results if not suppressed(lines, finding.line)),
        key=lambda finding: (finding.line, finding.rule),
    )
