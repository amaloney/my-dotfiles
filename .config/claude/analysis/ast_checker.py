#!/usr/bin/env python3
"""AST-based code analysis for finding common bugs and security issues.

Usage:
    python ast_checker.py [src_dir]
    python ast_checker.py --check underscore src/
    python ast_checker.py --check security src/
    python ast_checker.py --check all src/

Check Categories:
    bugs        - Common bug patterns (mutable defaults, unreachable code, etc.)
    security    - Security vulnerabilities (exec/eval, shell injection, etc.)
    quality     - Code quality (complexity, unused code, etc.)
    all         - Run all checks
"""

import argparse
import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Issue:
    """A detected code issue."""

    file: str
    line: int
    check: str
    category: str
    severity: str  # error, warning, info
    message: str
    suggestion: str | None = None


@dataclass
class FunctionInfo:
    """Information about a function for analysis."""

    name: str
    lineno: int
    args: set[str] = field(default_factory=set)
    used_names: set[str] = field(default_factory=set)
    return_count: int = 0
    max_depth: int = 0
    complexity: int = 1  # McCabe cyclomatic complexity


class DefinitionCollector(ast.NodeVisitor):
    """Collect all function, class, and variable definitions."""

    def __init__(self) -> None:
        self.functions: set[str] = set()
        self.classes: set[str] = set()
        self.variables: set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.functions.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.add(node.name)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variables.add(target.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name):
            self.variables.add(node.target.id)
        self.generic_visit(node)


class CallAnalyzer(ast.NodeVisitor):
    """Analyze function calls in a module."""

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.calls: list[tuple[str, int, str]] = []
        self.local_defs: set[str] = set()
        self.imports: set[str] = set()
        self.parameters: set[str] = set()
        self.current_function_params: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.local_defs.add(node.name)
        old_params = self.current_function_params
        self.current_function_params = {arg.arg for arg in node.args.args}
        self.parameters.update(self.current_function_params)
        self.generic_visit(node)
        self.current_function_params = old_params

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.local_defs.add(node.name)
        old_params = self.current_function_params
        self.current_function_params = {arg.arg for arg in node.args.args}
        self.parameters.update(self.current_function_params)
        self.generic_visit(node)
        self.current_function_params = old_params

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.local_defs.add(node.name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            self.calls.append((node.func.id, node.lineno, "function"))
        elif isinstance(node.func, ast.Attribute):
            self.calls.append((node.func.attr, node.lineno, "method"))
        self.generic_visit(node)


class BugChecker(ast.NodeVisitor):
    """Check for common bug patterns."""

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.issues: list[Issue] = []
        self.current_function: str | None = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node)

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        # Check mutable default arguments
        for default in node.args.defaults + node.args.kw_defaults:
            if default is None:
                continue
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.issues.append(
                    Issue(
                        file=str(self.filepath),
                        line=node.lineno,
                        check="mutable-default",
                        category="bugs",
                        severity="error",
                        message=f"Mutable default argument in '{node.name}'",
                        suggestion="Use None as default and initialize inside function",
                    )
                )

        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_Assert(self, node: ast.Assert) -> None:
        self.issues.append(
            Issue(
                file=str(self.filepath),
                line=node.lineno,
                check="assert-used",
                category="bugs",
                severity="warning",
                message="Assert statement (disabled with python -O)",
                suggestion="Use explicit if/raise for production validation",
            )
        )
        self.generic_visit(node)


class UnreachableCodeChecker(ast.NodeVisitor):
    """Check for unreachable code."""

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.issues: list[Issue] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_body(node.body)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_body(node.body)
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        # Check for if False: or if True:
        if isinstance(node.test, ast.Constant):
            if node.test.value is False:
                self.issues.append(
                    Issue(
                        file=str(self.filepath),
                        line=node.lineno,
                        check="unreachable-code",
                        category="bugs",
                        severity="warning",
                        message="Condition is always False",
                    )
                )
            elif node.test.value is True and node.orelse:
                self.issues.append(
                    Issue(
                        file=str(self.filepath),
                        line=node.orelse[0].lineno,
                        check="unreachable-code",
                        category="bugs",
                        severity="warning",
                        message="Else branch is unreachable (condition always True)",
                    )
                )
        self._check_body(node.body)
        self._check_body(node.orelse)
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        if isinstance(node.test, ast.Constant) and node.test.value is False:
            self.issues.append(
                Issue(
                    file=str(self.filepath),
                    line=node.lineno,
                    check="unreachable-code",
                    category="bugs",
                    severity="warning",
                    message="While condition is always False",
                )
            )
        self._check_body(node.body)
        self.generic_visit(node)

    def _check_body(self, body: list[ast.stmt]) -> None:
        """Check for code after return/break/continue/raise."""
        for i, stmt in enumerate(body):
            if isinstance(stmt, (ast.Return, ast.Break, ast.Continue, ast.Raise)):
                if i < len(body) - 1:
                    next_stmt = body[i + 1]
                    self.issues.append(
                        Issue(
                            file=str(self.filepath),
                            line=next_stmt.lineno,
                            check="unreachable-code",
                            category="bugs",
                            severity="error",
                            message=f"Unreachable code after {stmt.__class__.__name__.lower()}",
                        )
                    )


class UnusedChecker(ast.NodeVisitor):
    """Check for unused variables and arguments."""

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.issues: list[Issue] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node)

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        # Collect all parameter names (excluding self, cls, *args, **kwargs)
        params = set()
        for arg in node.args.args:
            if arg.arg not in ("self", "cls"):
                params.add(arg.arg)

        # Collect all names used in the function body
        used_names: set[str] = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                used_names.add(child.id)

        # Check for unused parameters (skip if name starts with _)
        for param in params:
            if param not in used_names and not param.startswith("_"):
                self.issues.append(
                    Issue(
                        file=str(self.filepath),
                        line=node.lineno,
                        check="unused-argument",
                        category="quality",
                        severity="info",
                        message=f"Unused argument '{param}' in '{node.name}'",
                        suggestion=f"Prefix with underscore: _{param}",
                    )
                )

        self.generic_visit(node)


class ExceptionChecker(ast.NodeVisitor):
    """Check for exception handling issues."""

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.issues: list[Issue] = []

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self.issues.append(
                Issue(
                    file=str(self.filepath),
                    line=node.lineno,
                    check="bare-except",
                    category="bugs",
                    severity="error",
                    message="Bare except clause",
                    suggestion="Catch specific exceptions: except Exception as exc:",
                )
            )
        self.generic_visit(node)


class SecurityChecker(ast.NodeVisitor):
    """Check for security vulnerabilities."""

    PASSWORD_PATTERNS = [
        re.compile(r"password", re.IGNORECASE),
        re.compile(r"passwd", re.IGNORECASE),
        re.compile(r"secret", re.IGNORECASE),
        re.compile(r"api_key", re.IGNORECASE),
        re.compile(r"apikey", re.IGNORECASE),
        re.compile(r"token", re.IGNORECASE),
        re.compile(r"auth", re.IGNORECASE),
    ]

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.issues: list[Issue] = []

    def visit_Call(self, node: ast.Call) -> None:
        func_name = self._get_func_name(node)

        # Check exec/eval/compile
        if func_name in ("exec", "eval", "compile"):
            self.issues.append(
                Issue(
                    file=str(self.filepath),
                    line=node.lineno,
                    check="exec-eval",
                    category="security",
                    severity="error",
                    message=f"Use of {func_name}() - potential code injection",
                    suggestion="Avoid dynamic code execution",
                )
            )

        # Check subprocess with shell=True
        if func_name in (
            "subprocess.run",
            "subprocess.call",
            "subprocess.Popen",
            "run",
            "call",
            "Popen",
        ):
            for keyword in node.keywords:
                if keyword.arg == "shell":
                    if (
                        isinstance(keyword.value, ast.Constant)
                        and keyword.value.value is True
                    ):
                        self.issues.append(
                            Issue(
                                file=str(self.filepath),
                                line=node.lineno,
                                check="shell-injection",
                                category="security",
                                severity="error",
                                message="subprocess with shell=True - shell injection risk",
                                suggestion="Use shell=False and pass args as list",
                            )
                        )

        # Check yaml.load without Loader
        if func_name in ("yaml.load", "load") and self._is_yaml_context(node):
            has_loader = any(kw.arg == "Loader" for kw in node.keywords)
            if not has_loader and len(node.args) < 2:
                self.issues.append(
                    Issue(
                        file=str(self.filepath),
                        line=node.lineno,
                        check="yaml-load",
                        category="security",
                        severity="error",
                        message="yaml.load() without Loader - arbitrary code execution risk",
                        suggestion="Use yaml.safe_load() or specify Loader=yaml.SafeLoader",
                    )
                )

        # Check pickle.load/loads
        if func_name in (
            "pickle.load",
            "pickle.loads",
            "load",
            "loads",
        ) and self._is_pickle_context(node):
            self.issues.append(
                Issue(
                    file=str(self.filepath),
                    line=node.lineno,
                    check="pickle-load",
                    category="security",
                    severity="warning",
                    message="Pickle deserialization - arbitrary code execution risk",
                    suggestion="Only unpickle data from trusted sources",
                )
            )

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        # Check for hardcoded passwords
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                if any(p.search(var_name) for p in self.PASSWORD_PATTERNS):
                    if isinstance(node.value, ast.Constant) and isinstance(
                        node.value.value, str
                    ):
                        if len(node.value.value) > 0:
                            self.issues.append(
                                Issue(
                                    file=str(self.filepath),
                                    line=node.lineno,
                                    check="hardcoded-password",
                                    category="security",
                                    severity="error",
                                    message=f"Hardcoded password/secret in '{var_name}'",
                                    suggestion="Use environment variables or secrets manager",
                                )
                            )
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        # Check for SQL injection patterns (string concatenation with SQL keywords)
        if isinstance(node.op, ast.Add):
            sql_pattern = re.compile(
                r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b", re.IGNORECASE
            )
            left_str = self._get_string_value(node.left)
            right_str = self._get_string_value(node.right)

            if left_str and sql_pattern.search(left_str):
                if isinstance(node.right, ast.Name) or isinstance(
                    node.right, ast.BinOp
                ):
                    self.issues.append(
                        Issue(
                            file=str(self.filepath),
                            line=node.lineno,
                            check="sql-injection",
                            category="security",
                            severity="error",
                            message="Potential SQL injection via string concatenation",
                            suggestion="Use parameterized queries",
                        )
                    )
        self.generic_visit(node)

    def _get_func_name(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return f"{node.func.value.id}.{node.func.attr}"
            return node.func.attr
        return ""

    def _is_yaml_context(self, node: ast.Call) -> bool:
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return node.func.value.id == "yaml"
        return False

    def _is_pickle_context(self, node: ast.Call) -> bool:
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return node.func.value.id == "pickle"
        return False

    def _get_string_value(self, node: ast.expr) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None


class QualityChecker(ast.NodeVisitor):
    """Check code quality metrics."""

    COMPLEXITY_THRESHOLD = 10
    MAX_RETURNS_THRESHOLD = 6
    MAX_DEPTH_THRESHOLD = 4

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.issues: list[Issue] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node)

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        # Count returns
        return_count = sum(1 for _ in ast.walk(node) if isinstance(_, ast.Return))
        if return_count > self.MAX_RETURNS_THRESHOLD:
            self.issues.append(
                Issue(
                    file=str(self.filepath),
                    line=node.lineno,
                    check="too-many-returns",
                    category="quality",
                    severity="info",
                    message=f"'{node.name}' has {return_count} return statements",
                    suggestion=f"Consider refactoring (threshold: {self.MAX_RETURNS_THRESHOLD})",
                )
            )

        # Calculate cyclomatic complexity
        complexity = self._calculate_complexity(node)
        if complexity > self.COMPLEXITY_THRESHOLD:
            self.issues.append(
                Issue(
                    file=str(self.filepath),
                    line=node.lineno,
                    check="complexity",
                    category="quality",
                    severity="warning",
                    message=f"'{node.name}' has complexity {complexity}",
                    suggestion=f"Consider refactoring (threshold: {self.COMPLEXITY_THRESHOLD})",
                )
            )

        # Check nesting depth
        max_depth = self._calculate_max_depth(node.body, 0)
        if max_depth > self.MAX_DEPTH_THRESHOLD:
            self.issues.append(
                Issue(
                    file=str(self.filepath),
                    line=node.lineno,
                    check="nested-depth",
                    category="quality",
                    severity="info",
                    message=f"'{node.name}' has nesting depth {max_depth}",
                    suggestion=f"Consider extracting nested logic (threshold: {self.MAX_DEPTH_THRESHOLD})",
                )
            )

        self.generic_visit(node)

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate McCabe cyclomatic complexity."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(
                child, (ast.If, ast.While, ast.For, ast.AsyncFor)
            ) or isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
                if child.ifs:
                    complexity += len(child.ifs)
        return complexity

    def _calculate_max_depth(self, body: list[ast.stmt], current_depth: int) -> int:
        """Calculate maximum nesting depth."""
        max_depth = current_depth
        for stmt in body:
            if isinstance(
                stmt,
                (
                    ast.If,
                    ast.For,
                    ast.While,
                    ast.AsyncFor,
                    ast.With,
                    ast.AsyncWith,
                    ast.Try,
                ),
            ):
                child_depth = current_depth + 1
                if isinstance(stmt, ast.If):
                    child_depth = max(
                        self._calculate_max_depth(stmt.body, current_depth + 1),
                        self._calculate_max_depth(stmt.orelse, current_depth + 1),
                    )
                elif isinstance(stmt, (ast.For, ast.While, ast.AsyncFor)) or isinstance(
                    stmt, (ast.With, ast.AsyncWith)
                ):
                    child_depth = self._calculate_max_depth(
                        stmt.body, current_depth + 1
                    )
                elif isinstance(stmt, ast.Try):
                    depths = [self._calculate_max_depth(stmt.body, current_depth + 1)]
                    for handler in stmt.handlers:
                        depths.append(
                            self._calculate_max_depth(handler.body, current_depth + 1)
                        )
                    if stmt.orelse:
                        depths.append(
                            self._calculate_max_depth(stmt.orelse, current_depth + 1)
                        )
                    if stmt.finalbody:
                        depths.append(
                            self._calculate_max_depth(stmt.finalbody, current_depth + 1)
                        )
                    child_depth = max(depths)
                max_depth = max(max_depth, child_depth)
        return max_depth


class StructureChecker(ast.NodeVisitor):
    """Check for file structure violations (constants placement, etc.)."""

    def __init__(self, filepath: Path, tree: ast.Module) -> None:
        self.filepath = filepath
        self.tree = tree
        self.issues: list[Issue] = []
        self.first_class_line: int | None = None
        self.class_names: set[str] = set()
        self.module_constants: list[tuple[str, int, ast.expr | None]] = []

    def check(self) -> None:
        """Run structure checks on module."""
        self._collect_class_info()
        self._collect_module_constants()
        self._check_constant_placement()

    def _collect_class_info(self) -> None:
        """Collect class names and first class line from module body."""
        for node in self.tree.body:
            if isinstance(node, ast.ClassDef):
                if self.first_class_line is None:
                    self.first_class_line = node.lineno
                self.class_names.add(node.name)

    def _collect_module_constants(self) -> None:
        """Collect module-level constant assignments (not inside classes/functions)."""
        for node in self.tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if name.isupper() or (
                            name.startswith("_") and name[1:].isupper()
                        ):
                            self.module_constants.append(
                                (name, node.lineno, node.value)
                            )

    def _references_class(self, value: ast.expr | None) -> bool:
        """Check if value references any defined class (e.g., enum values)."""
        if value is None:
            return False
        for node in ast.walk(value):
            if isinstance(node, ast.Attribute):
                if (
                    isinstance(node.value, ast.Name)
                    and node.value.id in self.class_names
                ):
                    return True
            if isinstance(node, ast.Name) and node.id in self.class_names:
                return True
        return False

    def _check_constant_placement(self) -> None:
        """Check that module constants are defined before first class."""
        if self.first_class_line is None:
            return

        for name, lineno, value in self.module_constants:
            if lineno > self.first_class_line:
                if self._references_class(value):
                    continue
                self.issues.append(
                    Issue(
                        file=str(self.filepath),
                        line=lineno,
                        check="constant-placement",
                        category="structure",
                        severity="warning",
                        message=f"Constant '{name}' defined after class (line {self.first_class_line})",
                        suggestion="Move constants to top of module after imports",
                    )
                )


class LoggingChecker(ast.NodeVisitor):
    """Check for logging anti-patterns."""

    LOGGER_METHODS = {
        "debug",
        "info",
        "warning",
        "error",
        "critical",
        "exception",
        "log",
    }

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.issues: list[Issue] = []

    def visit_Call(self, node: ast.Call) -> None:
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in self.LOGGER_METHODS
        ):
            # Check for %-formatting in logging
            if node.args:
                first_arg = node.args[0]
                if isinstance(first_arg, ast.BinOp) and isinstance(
                    first_arg.op, ast.Mod
                ):
                    self.issues.append(
                        Issue(
                            file=str(self.filepath),
                            line=node.lineno,
                            check="string-format-logging",
                            category="quality",
                            severity="info",
                            message="Use lazy % formatting in logging",
                            suggestion='Use logger.info("msg %s", var) instead of logger.info("msg %s" % var)',
                        )
                    )
                # Check for .format() in logging
                elif isinstance(first_arg, ast.Call):
                    if (
                        isinstance(first_arg.func, ast.Attribute)
                        and first_arg.func.attr == "format"
                    ):
                        self.issues.append(
                            Issue(
                                file=str(self.filepath),
                                line=node.lineno,
                                check="string-format-logging",
                                category="quality",
                                severity="info",
                                message="Use lazy formatting in logging",
                                suggestion='Use logger.info("msg %s", var) instead of logger.info("msg {}".format(var))',
                            )
                        )
        self.generic_visit(node)


def get_builtins() -> set[str]:
    """Get set of Python builtin names."""
    builtins = set()
    try:
        import builtins as b

        builtins = set(dir(b))
    except Exception:
        pass
    builtins.update(
        [
            "print",
            "len",
            "str",
            "int",
            "float",
            "list",
            "dict",
            "set",
            "tuple",
            "bool",
            "range",
            "enumerate",
            "zip",
            "map",
            "filter",
            "sorted",
            "reversed",
            "any",
            "all",
            "min",
            "max",
            "sum",
            "abs",
            "isinstance",
            "issubclass",
            "hasattr",
            "getattr",
            "setattr",
            "delattr",
            "callable",
            "type",
            "id",
            "repr",
            "hash",
            "iter",
            "next",
            "open",
            "super",
            "property",
            "staticmethod",
            "classmethod",
            "vars",
            "dir",
            "globals",
            "locals",
            "exec",
            "eval",
            "compile",
            "input",
            "format",
            "chr",
            "ord",
            "hex",
            "oct",
            "bin",
            "pow",
            "round",
            "divmod",
            "slice",
            "object",
            "Exception",
            "BaseException",
            "KeyError",
            "ValueError",
            "TypeError",
            "AttributeError",
            "ImportError",
            "RuntimeError",
            "StopIteration",
            "OSError",
            "FileNotFoundError",
            "NotImplementedError",
            "IndexError",
            "NameError",
            "AssertionError",
            "SyntaxError",
            "ZeroDivisionError",
            "OverflowError",
            "MemoryError",
        ]
    )
    return builtins


def collect_all_definitions(src_dir: Path) -> set[str]:
    """Collect all definitions across all Python files."""
    all_defs = set()
    for py_file in src_dir.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text())
            collector = DefinitionCollector()
            collector.visit(tree)
            all_defs.update(collector.functions)
            all_defs.update(collector.classes)
        except Exception:
            pass
    return all_defs


def check_underscore_typos(src_dir: Path) -> list[Issue]:
    """Find calls to _func() where func() exists but _func() doesn't."""
    all_defs = collect_all_definitions(src_dir)
    issues = []

    for py_file in src_dir.rglob("*.py"):
        try:
            source = py_file.read_text()
            tree = ast.parse(source)
            analyzer = CallAnalyzer(py_file)
            analyzer.visit(tree)

            for call_name, lineno, call_type in analyzer.calls:
                if call_name.startswith("_") and not call_name.startswith("__"):
                    without_underscore = call_name[1:]
                    if without_underscore in all_defs and call_name not in all_defs:
                        kind = "method" if call_type == "method" else "function"
                        issues.append(
                            Issue(
                                file=str(py_file.relative_to(src_dir)),
                                line=lineno,
                                check="underscore",
                                category="bugs",
                                severity="error",
                                message=f"'{call_name}' {kind} called but not defined",
                                suggestion=without_underscore,
                            )
                        )
        except SyntaxError:
            pass

    return issues


def check_undefined_calls(src_dir: Path) -> list[Issue]:
    """Find calls to functions that are not defined anywhere."""
    all_defs = collect_all_definitions(src_dir)
    builtins = get_builtins()
    issues = []

    for py_file in src_dir.rglob("*.py"):
        try:
            source = py_file.read_text()
            tree = ast.parse(source)
            analyzer = CallAnalyzer(py_file)
            analyzer.visit(tree)

            local_scope = (
                analyzer.local_defs
                | analyzer.imports
                | analyzer.parameters
                | builtins
                | all_defs
            )

            for call_name, lineno, call_type in analyzer.calls:
                if call_type == "method":
                    continue
                if call_name not in local_scope:
                    if call_name.startswith("_"):
                        continue
                    issues.append(
                        Issue(
                            file=str(py_file.relative_to(src_dir)),
                            line=lineno,
                            check="undefined",
                            category="bugs",
                            severity="error",
                            message=f"'{call_name}' is not defined",
                        )
                    )
        except SyntaxError:
            pass

    return issues


def run_file_checks(py_file: Path, src_dir: Path, categories: set[str]) -> list[Issue]:
    """Run all applicable checks on a single file."""
    issues = []
    try:
        source = py_file.read_text()
        tree = ast.parse(source)
        rel_path = py_file.relative_to(src_dir)

        if "bugs" in categories or "all" in categories:
            bug_checker = BugChecker(rel_path)
            bug_checker.visit(tree)
            issues.extend(bug_checker.issues)

            unreachable_checker = UnreachableCodeChecker(rel_path)
            unreachable_checker.visit(tree)
            issues.extend(unreachable_checker.issues)

            exception_checker = ExceptionChecker(rel_path)
            exception_checker.visit(tree)
            issues.extend(exception_checker.issues)

        if "security" in categories or "all" in categories:
            security_checker = SecurityChecker(rel_path)
            security_checker.visit(tree)
            issues.extend(security_checker.issues)

        if "quality" in categories or "all" in categories:
            unused_checker = UnusedChecker(rel_path)
            unused_checker.visit(tree)
            issues.extend(unused_checker.issues)

            quality_checker = QualityChecker(rel_path)
            quality_checker.visit(tree)
            issues.extend(quality_checker.issues)

            logging_checker = LoggingChecker(rel_path)
            logging_checker.visit(tree)
            issues.extend(logging_checker.issues)

        if "structure" in categories or "all" in categories:
            structure_checker = StructureChecker(rel_path, tree)
            structure_checker.check()
            issues.extend(structure_checker.issues)

    except SyntaxError:
        pass

    return issues


def run_checks(src_dir: Path, checks: list[str]) -> list[Issue]:
    """Run specified checks and return all issues."""
    all_issues = []
    categories = set(checks)

    # Cross-file checks
    if "underscore" in checks or "bugs" in categories or "all" in categories:
        all_issues.extend(check_underscore_typos(src_dir))

    if "undefined" in checks or "bugs" in categories or "all" in categories:
        all_issues.extend(check_undefined_calls(src_dir))

    # Per-file checks
    for py_file in src_dir.rglob("*.py"):
        all_issues.extend(run_file_checks(py_file, src_dir, categories))

    return sorted(all_issues, key=lambda x: (x.file, x.line))


def print_issues(issues: list[Issue], verbose: bool = False) -> None:
    """Print issues in a readable format."""
    if not issues:
        print("✓ No issues found!")
        return

    # Group by severity
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]

    print(
        f"Found {len(issues)} issue(s): {len(errors)} errors, {len(warnings)} warnings, {len(infos)} info\n"
    )

    current_file = None
    for issue in issues:
        if issue.file != current_file:
            current_file = issue.file
            print(f"\n{issue.file}:")

        severity_icon = {"error": "✗", "warning": "⚠", "info": "ℹ"}.get(
            issue.severity, "•"
        )
        print(f"  L{issue.line}: {severity_icon} [{issue.check}] {issue.message}")
        if issue.suggestion and verbose:
            print(f"         → {issue.suggestion}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AST-based code analysis for finding bugs and security issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Check Categories:
  bugs        Common bug patterns (mutable defaults, unreachable code, bare except)
  security    Security vulnerabilities (exec/eval, injection, hardcoded secrets)
  quality     Code quality (complexity, unused args, logging format)
  structure   File structure (constants placement)
  all         Run all checks (default)

Individual Checks:
  underscore  Find calls to _func() where func() exists (typo pattern)
  undefined   Find calls to functions not defined anywhere

Examples:
  %(prog)s src/
  %(prog)s --check bugs src/
  %(prog)s --check security --check quality src/
  %(prog)s -c underscore -c undefined src/
        """,
    )
    parser.add_argument(
        "src_dir",
        type=Path,
        nargs="?",
        default=Path("src"),
        help="Source directory to analyze (default: src/)",
    )
    parser.add_argument(
        "--check",
        "-c",
        action="append",
        dest="checks",
        choices=[
            "bugs",
            "security",
            "quality",
            "structure",
            "underscore",
            "undefined",
            "all",
        ],
        help="Check category or individual check to run",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show suggestions for each issue",
    )

    args = parser.parse_args()

    if not args.src_dir.exists():
        print(f"Error: {args.src_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    checks = args.checks or ["all"]
    issues = run_checks(args.src_dir, checks)

    if args.json:
        import json

        print(
            json.dumps(
                [
                    {
                        "file": i.file,
                        "line": i.line,
                        "check": i.check,
                        "category": i.category,
                        "severity": i.severity,
                        "message": i.message,
                        "suggestion": i.suggestion,
                    }
                    for i in issues
                ],
                indent=2,
            )
        )
    else:
        print_issues(issues, verbose=args.verbose)

    # Exit with error if any errors found
    has_errors = any(i.severity == "error" for i in issues)
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
