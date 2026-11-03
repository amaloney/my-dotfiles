#!/usr/bin/env python3
"""Flag cryptic names at every Python binding site.

Usage:
  naming_check.py PATH [PATH ...]   # CLI / CI / pre-commit -> exit 1 on findings
  naming_check.py --hook            # Claude Code hook: reads JSON on stdin -> exit 2 on findings
"""

import argparse
import ast
import json
import keyword
import sys
from pathlib import Path

ALLOWED = {"i", "j", "k", "_"}  # conventional index / throwaway names
CRYPTIC = {
    "ap",    # argument_parser
    "buf",   # buffer
    "cb",    # callback
    "cfg",   # config
    "col",   # column
    "ctx",   # context
    "db",    # database
    "dst",   # destination
    "elt",   # element
    "elts",  # elements
    "exc",   # exception
    "fh",    # file_handle
    "fn",    # function
    "fmt",   # format
    "hdr",   # header
    "idx",   # index
    "msg",   # message
    "num",   # number
    "obj",   # object
    "rec",   # record
    "req",   # request
    "resp",  # response
    "ret",   # result
    "src",   # source
    "tmp",   # temporary
    "val",   # value
    "var",   # variable
}
SUPPRESS = "# naming:allow"


def is_cryptic(name: str) -> bool:
    return name not in ALLOWED and (len(name) == 1 or name in CRYPTIC)


def singular(word: str | None) -> str | None:
    result = None

    if not word:
        return result

    if word.endswith("ies"):
        result = word[:-3] + "y"
    elif word.endswith(("ses", "xes", "ches", "shes")):
        result = word[:-2]
    elif word.endswith("s") and not word.endswith("ss"):
        result = word[:-1]
    if result and keyword.iskeyword(result):
        result += "_"

    return result


def base_name(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def call_name(node: ast.AST | None) -> str | None:
    return base_name(node.func) if isinstance(node, ast.Call) else None


def single_hint(src: ast.AST | None) -> str | None:
    func_name = call_name(src)
    if func_name == "range":
        return "index"
    if func_name == "keys":
        return "key"
    if func_name == "values":
        return singular(base_name(src.func.value)) or "value"
    if func_name in {"sorted", "reversed", "list", "set", "tuple", "iter"} and src.args:
        return single_hint(src.args[0])
    return singular(base_name(src))


def target_pairs(target: ast.AST, src) -> list[tuple[ast.Name, str | None]]:
    """Map each Name in a (possibly nested) loop target to a suggested name."""
    if isinstance(target, ast.Starred):
        target = target.value
    if isinstance(target, ast.Name):
        return [(target, src if isinstance(src, str) else single_hint(src))]
    if isinstance(target, (ast.Tuple, ast.List)):
        elements = target.elts
        sub_hints: list = [None] * len(elements)
        func_name = call_name(src)
        if func_name == "enumerate" and len(elements) == 2 and src.args:
            sub_hints = ["index", src.args[0]]
        elif func_name == "zip":
            sub_hints = (list(src.args) + sub_hints)[: len(elements)]
        elif func_name == "items" and len(elements) == 2:
            sub_hints = ["key", singular(base_name(src.func.value)) or "value"]
        return [pair for element, sub_hint in zip(elements, sub_hints) for pair in target_pairs(element, sub_hint)]
    return []


VERB_PREFIXES = ("get_", "find_", "fetch_", "load_", "read_", "build_", "make_", "create_", "parse_")


def value_hint(value: ast.AST | None) -> str | None:
    """`contact = get_contact_by_email(...)` -> `contact`."""
    name = call_name(value)
    if not name:
        return None
    name = name.lstrip("_")
    for prefix in VERB_PREFIXES:
        name = name.removeprefix(prefix)
    for separator in ("_by_", "_for_", "_from_"):
        name = name.split(separator, 1)[0]
    return name or None


def findings(tree: ast.AST):
    """Yield (lineno, column, site, name, hint) for every cryptic binding."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    yield target.lineno, target.col_offset, "assign", target.id, value_hint(node.value)
                else:
                    for name, hint in target_pairs(target, None):
                        yield name.lineno, name.col_offset, "assign", name.id, hint
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            yield node.target.lineno, node.target.col_offset, "assign", node.target.id, value_hint(node.value)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_args = node.args
            all_args = [*func_args.posonlyargs, *func_args.args, *func_args.kwonlyargs, func_args.vararg, func_args.kwarg]
            for arg in all_args:
                if arg:
                    yield arg.lineno, arg.col_offset, "parameter", arg.arg, None
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            for name, hint in target_pairs(node.target, node.iter):
                yield name.lineno, name.col_offset, "for", name.id, hint
        elif isinstance(node, ast.comprehension):
            for name, hint in target_pairs(node.target, node.iter):
                yield name.lineno, name.col_offset, "comprehension", name.id, hint
        elif isinstance(node, ast.Lambda):
            lambda_args = node.args
            all_args = [*lambda_args.posonlyargs, *lambda_args.args, *lambda_args.kwonlyargs, lambda_args.vararg, lambda_args.kwarg]
            for arg in all_args:
                if arg:
                    yield arg.lineno, arg.col_offset, "lambda", arg.arg, None
        elif isinstance(node, ast.ExceptHandler) and node.name:
            yield node.lineno, node.col_offset, "except", node.name, "error"
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                for name, _ in target_pairs(item.optional_vars, None) if item.optional_vars else []:
                    yield name.lineno, name.col_offset, "with", name.id, None
        elif isinstance(node, ast.NamedExpr):
            yield node.target.lineno, node.target.col_offset, "walrus", node.target.id, None
        elif isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
            yield node.lineno, node.col_offset, "match", node.name, None


def check_file(path: Path) -> list[str]:
    try:
        source = path.read_text()
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []  # never block on half-written or unreadable files
    lines = source.splitlines()
    output, seen = [], set()

    for lineno, column, site, name, hint in sorted(findings(tree)):
        if not is_cryptic(name) or (lineno, column) in seen:
            continue
        seen.add((lineno, column))
        if SUPPRESS in lines[lineno - 1]:
            continue
        tip = f" -> try `{hint}`" if hint and hint != name else ""
        output.append(f"{path}:{lineno}:{column + 1}: [{site}] `{name}` is cryptic{tip}")
    return output


def py_files(paths):
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            yield from sorted(path.rglob("*.py"))
        elif path.suffix == ".py":
            yield path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hook", action="store_true", help="read Claude Code hook JSON from stdin")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()

    if args.hook:
        payload = json.load(sys.stdin)
        file_path = payload.get("tool_input", {}).get("file_path", "")
        paths = [file_path] if file_path else []
    else:
        paths = args.paths

    problems = [message for file in py_files(paths) for message in check_file(file)]
    if problems:
        print("\n".join(problems), file=sys.stderr)
        print(
            f"naming: {len(problems)} finding(s). Rename, or append `{SUPPRESS}` to the line if intentional.",
            file=sys.stderr,
        )
        return 2 if args.hook else 1  # exit 2 = feed stderr back to Claude
    return 0


if __name__ == "__main__":
    sys.exit(main())
