#!/usr/bin/env python3
"""PostToolUse hook to check Python docstrings against vim-doge-helper standards.

Triggers on Edit events for .py files. Detects functions/methods that:
1. Have no docstring
2. Have a one-liner docstring (missing Args/Returns/Raises sections)

Usage in settings.json:
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.config/harnesses/scripts/docstring_check.py"
          }
        ]
      }
    ]
  }
}
"""

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

DOGE_HELPER = Path.home() / ".cargo" / "bin" / "vim-doge-helper"

# Skip docstring checks for infrastructure/harness code (both symlinks and targets)
EXCLUDED_PATHS = (
    str(Path.home() / ".config" / "harnesses"),
    str(Path.home() / ".claude" / "skills"),
    str(Path.home() / "Development" / "open-source" / "amaloney" / "my-dotfiles" / ".config" / "harnesses"),
)


def get_edited_file() -> str | None:
    """Get the file path from CLAUDE_FILE_PATH or CLAUDE_TOOL_INPUT env var.

    Returns:
        str | None: File path if available, None otherwise.
    """
    # Try CLAUDE_FILE_PATH first (set directly by Claude for file operations)
    file_path = os.environ.get("CLAUDE_FILE_PATH", "")
    if file_path:
        return file_path
    # Fall back to parsing CLAUDE_TOOL_INPUT JSON
    tool_input = os.environ.get("CLAUDE_TOOL_INPUT", "")
    if not tool_input:
        return None
    try:
        data = json.loads(tool_input)
        return data.get("file_path")
    except json.JSONDecodeError:
        return None


def is_google_style_docstring(docstring: str | None) -> bool:
    """Check if docstring follows Google style with Args/Returns/Raises sections."""
    if not docstring:
        return False
    # One-liners are not Google style
    lines = docstring.strip().split("\n")
    if len(lines) <= 1:
        return False
    # Must have at least one of Args:, Returns:, Raises:, or Yields:
    sections = ("Args:", "Returns:", "Raises:", "Yields:", "Attributes:", "Example:", "Examples:")
    return any(section in docstring for section in sections)


def has_parameters_or_meaningful_return(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if function has parameters (besides self/cls) or a non-None return annotation.

    Args:
        node (ast.FunctionDef | ast.AsyncFunctionDef): Function AST node to check.

    Returns:
        bool: True if the function needs Args/Returns sections in its docstring.
    """
    params = node.args
    # Check for non-self/cls parameters
    all_args = params.args + params.posonlyargs + params.kwonlyargs
    real_params = [arg for arg in all_args if arg.arg not in ("self", "cls")]
    if real_params or params.vararg or params.kwarg:
        return True
    # Check for return annotation (but not -> None)
    if node.returns is None:
        return False
    # Skip if return type is None (ast.Constant with value None)
    return not (isinstance(node.returns, ast.Constant) and node.returns.value is None)


def check_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict | None:
    """Check if a function needs a better docstring."""
    # Skip private/dunder methods
    if node.name.startswith("_") and not node.name.startswith("__init__"):
        return None

    docstring = ast.get_docstring(node)

    # No docstring at all
    if docstring is None:
        return {
            "line": node.lineno,
            "name": node.name,
            "issue": "missing",
        }

    # Has parameters/return but docstring is not Google style
    if has_parameters_or_meaningful_return(node) and not is_google_style_docstring(docstring):
        return {
            "line": node.lineno,
            "name": node.name,
            "issue": "incomplete",
            "current": docstring.split("\n")[0][:50],
        }

    return None


def generate_scaffold(filepath: str, line: int) -> list[str] | None:
    """Run vim-doge-helper to generate a docstring scaffold."""
    if not DOGE_HELPER.exists():
        return None
    try:
        result = subprocess.run(
            [
                str(DOGE_HELPER),
                "--filepath",
                filepath,
                "--parser",
                "python",
                "--doc-name",
                "google",
                "--line",
                str(line),
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            return data.get("docblock", [])
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return None


def check_file(filepath: str) -> list[dict]:
    """Check all functions in a Python file for docstring issues.

    Args:
        filepath (str): Path to the Python file to check.

    Returns:
        list[dict]: List of issue dictionaries with line, name, and issue keys.
    """
    # Skip infrastructure code
    resolved = str(Path(filepath).resolve())
    if any(resolved.startswith(excluded) for excluded in EXCLUDED_PATHS):
        return []

    issues = []
    try:
        source = Path(filepath).read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            issue = check_function(node)
            if issue:
                issues.append(issue)

    return issues


def main() -> int:
    filepath = get_edited_file()
    if not filepath or not filepath.endswith(".py"):
        return 0

    issues = check_file(filepath)
    if not issues:
        return 0

    # Output findings
    print("== docstring ==", file=sys.stderr)  # noqa: T201 CLI output
    for issue in issues[:5]:  # Limit to 5 to avoid noise
        if issue["issue"] == "missing":
            finding = f"{filepath}:{issue['line']}: `{issue['name']}` has no docstring"
        else:
            finding = f'{filepath}:{issue["line"]}: `{issue["name"]}` needs Args/Returns (has: "{issue["current"]}...")'

        # Try to generate scaffold hint
        scaffold = generate_scaffold(filepath, issue["line"])
        if scaffold:
            finding += " [scaffold available via vim-doge-helper]"

        print(finding, file=sys.stderr)  # noqa: T201 CLI output

    print(  # noqa: T201 CLI output
        "docstring-check: add Google-style docstrings with Args/Returns/Raises sections. "
        "Use `vim-doge-helper --filepath FILE --parser python --doc-name google --line N` "
        "to generate scaffolds.",
        file=sys.stderr,
    )

    # Return non-zero to block until docstrings are fixed
    return 1


if __name__ == "__main__":
    sys.exit(main())
