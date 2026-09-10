#!/usr/bin/env python3
"""Render a Jinja-templated markdown file to stdout."""

import sys
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
except ImportError:
    print("Error: jinja2 not installed. Run: pip install jinja2", file=sys.stderr)
    sys.exit(1)


def render_jinja_markdown(filepath: str, context: dict | None = None) -> str:
    path = Path(filepath).resolve()
    env = Environment(
        loader=FileSystemLoader(path.parent),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    template = env.get_template(path.name)
    return template.render(context or {})


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.md>", file=sys.stderr)
        sys.exit(1)
    print(render_jinja_markdown(sys.argv[1]))
