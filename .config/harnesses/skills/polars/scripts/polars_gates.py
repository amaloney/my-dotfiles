#!/usr/bin/env python3
"""Polars performance gates: static checks for documented slow or memory-hungry patterns.

Tiers:
  edit  PostToolUse hook: JSON on stdin, checks the edited file, exit 2 on `error` findings
  CLI   PATH [PATH ...]: checks the given files, exit 1 on any finding

Only files that import Polars are checked. Rules and evidence: references/gate-rules.md.

Usage:
  polars_gates.py --event edit
  polars_gates.py analysis.py notebook_cells.py --json
  polars_gates.py --explain POL002
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SUPPRESSION_PATTERN = re.compile(r"polars-gate:\s*allow\s+([A-Z0-9][A-Z0-9,\s]*)")
FILE_SUPPRESSION_PATTERN = re.compile(r"polars-gate:\s*allow-file\s+([A-Z0-9][A-Z0-9,\s]*)")

EAGER_READERS = frozenset(
    {"read_csv", "read_parquet", "read_json", "read_ndjson", "read_ipc", "read_avro", "read_delta"}
)
PANDAS_READERS = frozenset(
    {"read_csv", "read_parquet", "read_json", "read_excel", "read_sql", "read_feather", "read_pickle"}
)
PYTHON_CALLABLE_METHODS = frozenset({"map_elements", "apply", "map_groups"})
ROW_LOOP_METHODS = frozenset({"iter_rows", "iterrows"})
PANDAS_SPELLINGS = frozenset({"groupby", "iloc"})
EXPANDABLE_CONTEXTS = frozenset({"select", "with_columns", "agg"})
CHAINED_OPS = frozenset(
    {
        "filter",
        "select",
        "with_columns",
        "group_by",
        "agg",
        "sort",
        "join",
        "head",
        "tail",
        "unique",
        "drop_nulls",
        "fill_null",
        "cast",
        "rename",
        "explode",
        "slice",
        "to_pandas",
        "write_parquet",
        "write_csv",
    }
)


@dataclass(frozen=True)
class Rule:
    code: str
    severity: str
    summary: str
    hint: str


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    column: int
    rule: Rule
    detail: str

    def as_line(self) -> str:
        reference = f"references/gate-rules.md#{self.rule.code.lower()}"
        detail = f" ({self.detail})" if self.detail else ""
        location = f"{self.path}:{self.line}:{self.column}"
        message = f"{self.rule.code} {self.rule.severity}: {self.rule.summary}{detail}"
        return f"{location}: {message} [{reference}]"


RULES: dict[str, Rule] = {
    "POL001": Rule(
        "POL001",
        "error",
        "eager read_* materializes before the optimizer runs; use the matching scan_* source",
        "Sources and sinks: favor scan_* over read_*",
    ),
    "POL002": Rule(
        "POL002",
        "error",
        "Python callable inside the query; rewrite as a native expression",
        "UDF docs: map_elements calls Python per value and disables optimization",
    ),
    "POL003": Rule(
        "POL003",
        "hint",
        "map_batches runs one Python call per Series; keep only for compiled ufuncs",
        "UDF docs: prefer expressions; ufuncs/numba are the exception",
    ),
    "POL004": Rule(
        "POL004",
        "error",
        "row-wise iteration is the slowest access shape; use expressions",
        "Polars skill: expressions over Python loops",
    ),
    "POL005": Rule(
        "POL005",
        "hint",
        "to_pandas copies out of Arrow; convert only at a library boundary",
        "Interop boundary is the legitimate case",
    ),
    "POL006": Rule(
        "POL006",
        "hint",
        "pandas reader inside a Polars file; prefer the scan_* source",
        "Avoid a pandas roundtrip before Polars",
    ),
    "POL007": Rule(
        "POL007",
        "error",
        "collect() mid-chain materializes and discards the plan; collect once at the end",
        "Polars skill: collect exactly once per query",
    ),
    "POL008": Rule(
        "POL008",
        "hint",
        "list comprehension of per-column expressions serializes; expand one expression instead",
        "One context runs its expressions in parallel",
    ),
    "POL009": Rule(
        "POL009",
        "error",
        "pandas API spelling in a Polars file; this is not the Polars API",
        "groupby/iterrows/iloc do not exist in Polars",
    ),
    "POL010": Rule(
        "POL010",
        "error",
        "suppressing Polars warnings hides the documented performance fix",
        "Polars warnings name the fix; apply it instead",
    ),
}

RULE_ORDER = list(RULES)


def dotted_name(node: ast.AST) -> str | None:
    """Resolve a Name/Attribute chain to a dotted string.

    Args:
        node: AST node to resolve.

    Returns:
        Dotted name such as `pl.read_csv`, or None when the chain is not static.
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def import_bindings(tree: ast.Module) -> tuple[set[str], set[str], set[str], set[str]]:
    """Collect local names bound to the polars module, polars functions, pandas module, pandas functions.

    Args:
        tree: Parsed module.

    Returns:
        `(polars_modules, polars_functions, pandas_modules, pandas_functions)`.
    """
    polars_modules: set[str] = set()
    polars_functions: set[str] = set()
    pandas_modules: set[str] = set()
    pandas_functions: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                local = alias.asname or root
                if root == "polars":
                    polars_modules.add(local)
                elif root == "pandas":
                    pandas_modules.add(local)
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            for alias in node.names:
                local = alias.asname or alias.name
                if root == "polars":
                    polars_functions.add(local)
                elif root == "pandas":
                    pandas_functions.add(local)
    return polars_modules, polars_functions, pandas_modules, pandas_functions


def load_suppressions(lines: list[str]) -> tuple[set[str], dict[int, set[str]]]:
    """Parse `# polars-gate: allow[-file] CODE` comments.

    Args:
        lines: File lines.

    Returns:
        `(file_wide_codes, {line_number: codes})`.
    """
    file_codes: set[str] = set()
    line_codes: dict[int, set[str]] = {}
    if lines:
        match = FILE_SUPPRESSION_PATTERN.search(lines[0])
        if match:
            file_codes.update(code.strip() for code in match.group(1).split(",") if code.strip())
    for number, text in enumerate(lines, start=1):
        marker = text.find("#")
        if marker == -1:
            continue
        match = SUPPRESSION_PATTERN.search(text[marker:])
        if match:
            line_codes.setdefault(number, set()).update(
                code.strip() for code in match.group(1).split(",") if code.strip()
            )
    return file_codes, line_codes


class PolarsGateVisitor(ast.NodeVisitor):
    """Collect candidate findings; suppression is applied by the caller."""

    def __init__(
        self,
        path: Path,
        polars_modules: set[str],
        polars_functions: set[str],
        pandas_modules: set[str],
        pandas_functions: set[str],
    ) -> None:
        self.path = path
        self.polars_modules = polars_modules
        self.polars_functions = polars_functions
        self.pandas_modules = pandas_modules
        self.pandas_functions = pandas_functions
        self.findings: list[Finding] = []

    def add(self, node: ast.AST, code: str, detail: str = "") -> None:
        self.findings.append(
            Finding(
                path=self.path,
                line=getattr(node, "lineno", 0),
                column=getattr(node, "col_offset", 0) + 1,
                rule=RULES[code],
                detail=detail,
            )
        )

    def visit_Call(self, node: ast.Call) -> None:
        name = dotted_name(node.func) or ""
        prefix, _, attribute = name.rpartition(".")
        root = prefix.split(".")[0] if prefix else ""

        if root in self.polars_modules and attribute in EAGER_READERS:
            self.add(node, "POL001", f"pl.{attribute}")
        if name in self.polars_functions and name in EAGER_READERS:
            self.add(node, "POL001", name)
        if root in self.pandas_modules and attribute in PANDAS_READERS:
            self.add(node, "POL006", f"pd.{attribute}")
        if name in self.pandas_functions and name in PANDAS_READERS:
            self.add(node, "POL006", name)

        if isinstance(node.func, ast.Attribute):
            method = node.func.attr
            if method in PYTHON_CALLABLE_METHODS:
                self.add(node, "POL002", f".{method}()")
            elif method == "map_batches":
                self.add(node, "POL003", ".map_batches()")
            elif method in ROW_LOOP_METHODS:
                self.add(node, "POL004", f".{method}()")
            elif method == "to_pandas":
                self.add(node, "POL005", ".to_pandas()")
            elif method in EXPANDABLE_CONTEXTS and any(
                isinstance(argument, (ast.ListComp, ast.GeneratorExp)) for argument in node.args
            ):
                self.add(node, "POL008", f".{method}([...comprehension])")

        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Call):
            inner = node.func.value
            if isinstance(inner.func, ast.Attribute) and inner.func.attr == "collect" and node.func.attr in CHAINED_OPS:
                self.add(node, "POL007", f".collect().{node.func.attr}()")

        if name.endswith("filterwarnings") or name.endswith("simplefilter"):
            first = node.args[0] if node.args else None
            if isinstance(first, ast.Constant) and first.value == "ignore":
                self.add(node, "POL010", f"{name}(...ignore)")

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in PANDAS_SPELLINGS:
            self.add(node, "POL009", f".{node.attr}")
        self.generic_visit(node)


def check_file(path: Path) -> tuple[list[Finding], int]:
    """Check one Python file for Polars performance anti-patterns.

    Args:
        path: File to check.

    Returns:
        `(findings, suppressed_count)`; empty findings for non-Polars or unparsable files.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return [], 0
    if "polars" not in source:
        return [], 0
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return [], 0

    polars_modules, polars_functions, pandas_modules, pandas_functions = import_bindings(tree)
    if not polars_modules and not polars_functions:
        return [], 0

    visitor = PolarsGateVisitor(path, polars_modules, polars_functions, pandas_modules, pandas_functions)
    visitor.visit(tree)
    file_codes, line_codes = load_suppressions(source.splitlines())

    findings: list[Finding] = []
    suppressed = 0
    for finding in visitor.findings:
        allowed = finding.rule.code in file_codes or finding.rule.code in line_codes.get(finding.line, set())
        if allowed:
            suppressed += 1
        else:
            findings.append(finding)
    findings.sort(key=lambda finding: (finding.line, finding.column, RULE_ORDER.index(finding.rule.code)))
    return findings, suppressed


def event_paths() -> list[Path]:
    """Read a PostToolUse payload from stdin and extract the edited file path.

    Args:
        None.

    Returns:
        Zero or one path.
    """
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return []
    file_path = payload.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return []
    path = Path(file_path)
    return [path] if path.suffix in {".py", ".pyi"} and path.is_file() else []


def run(paths: list[Path], errors_only: bool, as_json: bool) -> int:
    """Print findings and return an exit status.

    Args:
        paths: Files to check.
        errors_only: Ignore `hint` findings for reporting and exit status.
        as_json: Emit machine-readable output.

    Returns:
        1 when findings remain, else 0.
    """
    findings: list[Finding] = []
    suppressed_total = 0
    for path in paths:
        file_findings, suppressed = check_file(path)
        suppressed_total += suppressed
        findings.extend(finding for finding in file_findings if not errors_only or finding.rule.severity == "error")

    if as_json:
        payload = {
            "findings": [
                {
                    "path": str(finding.path),
                    "line": finding.line,
                    "column": finding.column,
                    "code": finding.rule.code,
                    "severity": finding.rule.severity,
                    "message": finding.rule.summary,
                    "hint": finding.rule.hint,
                }
                for finding in findings
            ],
            "suppressed": suppressed_total,
        }
        print(json.dumps(payload, indent=2))
    else:
        for finding in findings:
            print(finding.as_line(), file=sys.stderr)
        if findings:
            print(
                f"polars-gates: {len(findings)} finding(s), {suppressed_total} suppressed. "
                "Fix or annotate with `# polars-gate: allow CODE`.",
                file=sys.stderr,
            )
    return 1 if findings else 0


def explain(code: str) -> int:
    """Print one rule's rationale.

    Args:
        code: Rule code such as `POL002`.

    Returns:
        Process exit status.
    """
    rule = RULES.get(code.upper())
    if rule is None:
        print(f"unknown rule: {code}", file=sys.stderr)
        print("known rules: " + ", ".join(RULE_ORDER), file=sys.stderr)
        return 2
    print(f"{rule.code} ({rule.severity}): {rule.summary}")
    print(f"why: {rule.hint}")
    print(f"reference: references/gate-rules.md#{rule.code.lower()}")
    return 0


def main() -> int:
    """Entry point for hook and CLI use.

    Args:
        None.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", choices=["edit"], help="run as a PostToolUse hook")
    parser.add_argument("--errors-only", action="store_true", help="ignore hint-severity findings")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--explain", metavar="CODE", help="print a rule's rationale")
    parser.add_argument("paths", nargs="*")
    arguments = parser.parse_args()

    if arguments.explain:
        return explain(arguments.explain)

    if arguments.event == "edit":
        findings_paths = event_paths()
        if not findings_paths:
            return 0
        status = run(findings_paths, errors_only=True, as_json=False)
        return 2 if status else 0

    paths = [Path(candidate) for candidate in arguments.paths if candidate.endswith((".py", ".pyi"))]
    existing = [path for path in paths if path.is_file()]
    if not existing:
        print("polars-gates: no Python files to check", file=sys.stderr)
        return 0
    return run(existing, errors_only=arguments.errors_only, as_json=arguments.json)


if __name__ == "__main__":
    sys.exit(main())
