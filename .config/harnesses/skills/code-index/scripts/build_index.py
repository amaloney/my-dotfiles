#!/usr/bin/env python3
"""Build a semantic code index for the repository.

Scans source files, extracts classes/methods/functions, and stores
them in a ChromaDB vector database for semantic search.

Configuration is read from index_config.json in the same directory.
"""

import ast
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("ChromaDB not installed. Install with: pip install chromadb")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "index_config.json"
DEFAULT_CONFIG = {
    "source_patterns": ["**/*.py"],
    "exclude_patterns": [
        "**/test_*.py",
        "**/*_test.py",
        "**/conftest.py",
        "**/__pycache__/**",
    ],
    "collection_name": "code_entities",
}


def load_config() -> dict:
    """Load configuration from index_config.json."""
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return DEFAULT_CONFIG


@dataclass
class CodeEntity:
    """Represents a class, method, or function extracted from code."""

    name: str
    entity_type: str
    file_path: str
    line_number: int
    signature: str
    docstring: str | None
    parent_class: str | None
    source_code: str
    decorators: list[str]

    def to_searchable_text(self) -> str:
        """Create searchable text representation."""
        parts = [f"{self.entity_type}: {self.name}", f"signature: {self.signature}"]
        if self.parent_class:
            parts.append(f"class: {self.parent_class}")
        if self.docstring:
            parts.append(f"description: {self.docstring}")
        if self.decorators:
            parts.append(f"decorators: {', '.join(self.decorators)}")
        parts.append(f"code: {self.source_code}")
        return "\n".join(parts)

    def get_id(self) -> str:
        """Generate unique ID for this entity."""
        key = f"{self.file_path}:{self.name}:{self.line_number}"
        return hashlib.md5(key.encode()).hexdigest()


class CodeExtractor(ast.NodeVisitor):
    """Extract code entities from Python AST."""

    def __init__(self, file_path: str, source_lines: list[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.entities: list[CodeEntity] = []
        self.current_class: str | None = None

    def get_source(self, node: ast.AST) -> str:
        """Extract source code for a node."""
        try:
            return ast.get_source_segment("\n".join(self.source_lines), node) or ""
        except Exception:
            if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                return "\n".join(self.source_lines[node.lineno - 1 : node.end_lineno])
            return ""

    def get_decorators(self, node) -> list[str]:
        """Extract decorator names."""
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(dec.attr)
            elif isinstance(dec, ast.Call):
                func = dec.func
                if isinstance(func, ast.Name):
                    decorators.append(func.id)
                elif isinstance(func, ast.Attribute):
                    decorators.append(func.attr)
        return decorators

    def get_signature(self, node) -> str:
        """Build function signature string."""
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                try:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                except Exception:
                    pass
            args.append(arg_str)

        for i, default in enumerate(reversed(node.args.defaults)):
            idx = len(args) - i - 1
            if idx >= 0:
                try:
                    args[idx] += f" = {ast.unparse(default)}"
                except Exception:
                    pass

        sig = f"def {node.name}({', '.join(args)})"
        if node.returns:
            try:
                sig += f" -> {ast.unparse(node.returns)}"
            except Exception:
                pass
        return sig

    def visit_ClassDef(self, node: ast.ClassDef):
        """Extract class definition."""
        bases = []
        for base in node.bases:
            try:
                bases.append(ast.unparse(base))
            except Exception:
                pass

        signature = f"class {node.name}"
        if bases:
            signature += f"({', '.join(bases)})"

        self.entities.append(
            CodeEntity(
                name=node.name,
                entity_type="class",
                file_path=self.file_path,
                line_number=node.lineno,
                signature=signature,
                docstring=ast.get_docstring(node),
                parent_class=None,
                source_code=self.get_source(node),
                decorators=self.get_decorators(node),
            )
        )

        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._extract_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._extract_function(node, is_async=True)
        self.generic_visit(node)

    def _extract_function(self, node, is_async: bool = False):
        """Extract function or method."""
        entity_type = "method" if self.current_class else "function"
        sig = self.get_signature(node)
        if is_async:
            sig = "async " + sig

        self.entities.append(
            CodeEntity(
                name=node.name,
                entity_type=entity_type,
                file_path=self.file_path,
                line_number=node.lineno,
                signature=sig,
                docstring=ast.get_docstring(node),
                parent_class=self.current_class,
                source_code=self.get_source(node),
                decorators=self.get_decorators(node),
            )
        )


def extract_entities_from_file(file_path: Path) -> list[CodeEntity]:
    """Parse a Python file and extract all code entities."""
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        extractor = CodeExtractor(str(file_path), source.splitlines())
        extractor.visit(tree)
        return extractor.entities
    except SyntaxError as e:
        print(f"  Syntax error in {file_path}: {e}")
        return []
    except Exception as e:
        print(f"  Error processing {file_path}: {e}")
        return []


def matches_pattern(path: Path, patterns: list[str], root: Path) -> bool:
    """Check if path matches any of the glob patterns."""
    rel_path = path.relative_to(root)
    for pattern in patterns:
        if rel_path.match(pattern):
            return True
    return False


def build_index(project_root: Path, db_dir: Path, config: dict):
    """Build the semantic index for source files."""
    print(f"Scanning {project_root}...")

    client = chromadb.PersistentClient(
        path=str(db_dir),
        settings=Settings(anonymized_telemetry=False),
    )

    collection_name = config.get("collection_name", "code_entities")
    try:
        client.delete_collection(collection_name)
        print("Cleared existing collection")
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"description": f"Code entities from {project_root.name}"},
    )

    all_entities: list[CodeEntity] = []
    source_files = []

    for pattern in config.get("source_patterns", ["**/*.py"]):
        source_files.extend(project_root.rglob(pattern.lstrip("*/")))

    exclude_patterns = config.get("exclude_patterns", [])
    source_files = [
        f
        for f in source_files
        if f.is_file() and not matches_pattern(f, exclude_patterns, project_root)
    ]

    for src_file in sorted(set(source_files)):
        entities = extract_entities_from_file(src_file)
        all_entities.extend(entities)
        if entities:
            print(f"  {src_file.relative_to(project_root)}: {len(entities)} entities")

    if not all_entities:
        print("No entities found!")
        return

    print(f"\nIndexing {len(all_entities)} entities...")

    batch_size = 100
    for i in range(0, len(all_entities), batch_size):
        batch = all_entities[i : i + batch_size]
        collection.add(
            ids=[e.get_id() for e in batch],
            documents=[e.to_searchable_text() for e in batch],
            metadatas=[
                {
                    "name": e.name,
                    "type": e.entity_type,
                    "file": e.file_path,
                    "line": e.line_number,
                    "signature": e.signature,
                    "parent_class": e.parent_class or "",
                    "decorators": ",".join(e.decorators),
                }
                for e in batch
            ],
        )

    stats = {
        "classes": sum(1 for e in all_entities if e.entity_type == "class"),
        "methods": sum(1 for e in all_entities if e.entity_type == "method"),
        "functions": sum(1 for e in all_entities if e.entity_type == "function"),
        "total": len(all_entities),
        "files": len(source_files),
    }

    (db_dir / "stats.json").write_text(json.dumps(stats, indent=2))

    print("\nIndex built successfully!")
    print(f"  Classes: {stats['classes']}")
    print(f"  Methods: {stats['methods']}")
    print(f"  Functions: {stats['functions']}")
    print(f"  Total: {stats['total']} entities from {stats['files']} files")


if __name__ == "__main__":
    config = load_config()
    project_root = SCRIPT_DIR.parent.parent
    db_dir = SCRIPT_DIR / "chroma_db"

    if not project_root.exists():
        print(f"Project root not found: {project_root}")
        sys.exit(1)

    build_index(project_root, db_dir, config)
