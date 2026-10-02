#!/usr/bin/env python3
"""Build bi-temporal code knowledge graph.

Extracts code entities and relationships with temporal tracking from git history.
Stores in SQLite (temporal/relational queries) + ChromaDB (semantic search).
"""

import ast
import hashlib
import json
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple, Dict

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("ChromaDB not installed. Install with: pip install chromadb")
    sys.exit(1)


@dataclass
class CodeEntity:
    """Code entity with bi-temporal tracking."""
    name: str
    entity_type: str
    qualified_name: str
    file_path: str
    line_start: int
    line_end: Optional[int]
    signature: Optional[str]
    docstring: Optional[str]
    parent_id: Optional[str]
    decorators: List[str]
    is_async: bool = False
    is_property: bool = False
    source_code: str = ""

    # Bi-temporal (populated from git)
    valid_from: str = ""
    valid_until: Optional[str] = None
    commit_sha_from: str = ""
    commit_sha_until: Optional[str] = None
    indexed_at: str = ""

    def get_id(self) -> str:
        key = f"{self.qualified_name}:{self.line_start}"
        return hashlib.md5(key.encode()).hexdigest()

    def to_searchable_text(self) -> str:
        parts = [f"{self.entity_type}: {self.name}", f"qualified: {self.qualified_name}"]
        if self.signature:
            parts.append(f"signature: {self.signature}")
        if self.docstring:
            parts.append(f"description: {self.docstring}")
        if self.decorators:
            parts.append(f"decorators: {', '.join(self.decorators)}")
        if self.source_code:
            parts.append(f"code: {self.source_code[:500]}")
        return "\n".join(parts)


@dataclass
class CodeRelation:
    """Relationship between code entities."""
    source_id: str
    target_id: Optional[str]
    target_name: str
    rel_type: str  # calls, inherits, imports, uses_type, decorates, returns, raises
    line_number: Optional[int]
    valid_from: str = ""
    valid_until: Optional[str] = None
    commit_sha_from: str = ""


class RelationExtractor(ast.NodeVisitor):
    """Extract relationships from AST."""

    def __init__(self, source_id: str, file_path: str):
        self.source_id = source_id
        self.file_path = file_path
        self.relations: List[CodeRelation] = []
        self.current_function: Optional[str] = None

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.relations.append(CodeRelation(
                source_id=self.source_id,
                target_id=None,
                target_name=alias.name,
                rel_type="imports",
                line_number=node.lineno,
            ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            name = f"{module}.{alias.name}" if module else alias.name
            self.relations.append(CodeRelation(
                source_id=self.source_id,
                target_id=None,
                target_name=name,
                rel_type="imports",
                line_number=node.lineno,
            ))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        target = self._get_call_name(node.func)
        if target:
            self.relations.append(CodeRelation(
                source_id=self.source_id,
                target_id=None,
                target_name=target,
                rel_type="calls",
                line_number=node.lineno,
            ))
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        for base in node.bases:
            base_name = self._get_name(base)
            if base_name:
                self.relations.append(CodeRelation(
                    source_id=self.source_id,
                    target_id=None,
                    target_name=base_name,
                    rel_type="inherits",
                    line_number=node.lineno,
                ))
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise):
        if node.exc:
            exc_name = self._get_name(node.exc)
            if exc_name:
                self.relations.append(CodeRelation(
                    source_id=self.source_id,
                    target_id=None,
                    target_name=exc_name,
                    rel_type="raises",
                    line_number=node.lineno,
                ))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._extract_return_type(node)
        self._extract_arg_types(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._extract_return_type(node)
        self._extract_arg_types(node)
        self.generic_visit(node)

    def _extract_return_type(self, node):
        if node.returns:
            ret_type = self._get_name(node.returns)
            if ret_type and not ret_type.startswith(("str", "int", "float", "bool", "None")):
                self.relations.append(CodeRelation(
                    source_id=self.source_id,
                    target_id=None,
                    target_name=ret_type,
                    rel_type="returns",
                    line_number=node.lineno,
                ))

    def _extract_arg_types(self, node):
        for arg in node.args.args:
            if arg.annotation:
                type_name = self._get_name(arg.annotation)
                if type_name and not type_name.startswith(("str", "int", "float", "bool", "None", "Any")):
                    self.relations.append(CodeRelation(
                        source_id=self.source_id,
                        target_id=None,
                        target_name=type_name,
                        rel_type="uses_type",
                        line_number=node.lineno,
                    ))

    def _get_call_name(self, node) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_name(node.value)
            if value:
                return f"{value}.{node.attr}"
            return node.attr
        elif isinstance(node, ast.Call):
            return self._get_call_name(node.func)
        return None

    def _get_name(self, node) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_name(node.value)
            if value:
                return f"{value}.{node.attr}"
            return node.attr
        elif isinstance(node, ast.Subscript):
            return self._get_name(node.value)
        elif isinstance(node, ast.Call):
            return self._get_call_name(node.func)
        return None


class CodeExtractor(ast.NodeVisitor):
    """Extract code entities with relationship tracking."""

    def __init__(self, file_path: str, source_lines: List[str], module_name: str):
        self.file_path = file_path
        self.source_lines = source_lines
        self.module_name = module_name
        self.entities: List[CodeEntity] = []
        self.relations: List[CodeRelation] = []
        self.current_class: Optional[str] = None
        self.class_stack: List[str] = []

    def get_qualified_name(self, name: str) -> str:
        if self.current_class:
            return f"{self.module_name}.{self.current_class}.{name}"
        return f"{self.module_name}.{name}"

    def get_source(self, node: ast.AST) -> str:
        try:
            return ast.get_source_segment("\n".join(self.source_lines), node) or ""
        except Exception:
            if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                return "\n".join(self.source_lines[node.lineno - 1:node.end_lineno])
            return ""

    def get_decorators(self, node) -> List[str]:
        decorators = []
        for dec in getattr(node, "decorator_list", []):
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(dec.attr)
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)
                elif isinstance(dec.func, ast.Attribute):
                    decorators.append(dec.func.attr)
        return decorators

    def get_signature(self, node) -> str:
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                try:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                except Exception:
                    pass
            args.append(arg_str)

        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        sig = f"{prefix} {node.name}({', '.join(args)})"
        if node.returns:
            try:
                sig += f" -> {ast.unparse(node.returns)}"
            except Exception:
                pass
        return sig

    def visit_ClassDef(self, node: ast.ClassDef):
        qualified = self.get_qualified_name(node.name)
        bases = [ast.unparse(b) for b in node.bases if hasattr(ast, "unparse")]

        entity = CodeEntity(
            name=node.name,
            entity_type="class",
            qualified_name=qualified,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=node.end_lineno,
            signature=f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}",
            docstring=ast.get_docstring(node),
            parent_id=None,
            decorators=self.get_decorators(node),
            source_code=self.get_source(node),
        )
        self.entities.append(entity)

        # Extract class-level relations
        extractor = RelationExtractor(entity.get_id(), self.file_path)
        for base in node.bases:
            base_name = extractor._get_name(base)
            if base_name:
                self.relations.append(CodeRelation(
                    source_id=entity.get_id(),
                    target_id=None,
                    target_name=base_name,
                    rel_type="inherits",
                    line_number=node.lineno,
                ))

        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._extract_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._extract_function(node, is_async=True)

    def _extract_function(self, node, is_async: bool = False):
        qualified = self.get_qualified_name(node.name)
        decorators = self.get_decorators(node)

        entity = CodeEntity(
            name=node.name,
            entity_type="method" if self.current_class else "function",
            qualified_name=qualified,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=node.end_lineno,
            signature=self.get_signature(node),
            docstring=ast.get_docstring(node),
            parent_id=None,  # Will be resolved later
            decorators=decorators,
            is_async=is_async,
            is_property="property" in decorators,
            source_code=self.get_source(node),
        )
        self.entities.append(entity)

        # Extract relations from function body
        extractor = RelationExtractor(entity.get_id(), self.file_path)
        extractor.visit(node)
        self.relations.extend(extractor.relations)

        self.generic_visit(node)


def get_git_info(repo_path: Path) -> Tuple[str, str]:
    """Get current commit SHA and timestamp."""
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path, text=True, stderr=subprocess.DEVNULL
        ).strip()
        timestamp = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI"],
            cwd=repo_path, text=True, stderr=subprocess.DEVNULL
        ).strip()
        return sha, timestamp
    except Exception:
        now = datetime.now().isoformat()
        return "unknown", now


def get_file_first_commit(file_path: Path, repo_path: Path) -> Tuple[str, str]:
    """Get the first commit that introduced a file."""
    try:
        rel_path = file_path.relative_to(repo_path)
        result = subprocess.check_output(
            ["git", "log", "--follow", "--format=%H %cI", "--diff-filter=A", "--", str(rel_path)],
            cwd=repo_path, text=True, stderr=subprocess.DEVNULL
        ).strip()
        if result:
            lines = result.strip().split("\n")
            if lines:
                parts = lines[-1].split(" ", 1)
                return parts[0], parts[1] if len(parts) > 1 else ""
    except Exception:
        pass
    return get_git_info(repo_path)


def extract_from_file(file_path: Path, repo_path: Path) -> tuple[List[CodeEntity], List[CodeRelation]]:
    """Extract entities and relations from a Python file."""
    try:
        source = file_path.read_text(encoding="utf-8")
        source_lines = source.splitlines()
        tree = ast.parse(source)

        # Calculate module name
        rel_path = file_path.relative_to(repo_path / "src")
        module_name = str(rel_path.with_suffix("")).replace("/", ".").replace("\\", ".")

        extractor = CodeExtractor(str(file_path), source_lines, module_name)
        extractor.visit(tree)

        # Add temporal info
        commit_sha, commit_time = get_file_first_commit(file_path, repo_path)
        indexed_at = datetime.now().isoformat()

        for entity in extractor.entities:
            entity.valid_from = commit_time
            entity.commit_sha_from = commit_sha
            entity.indexed_at = indexed_at

        for relation in extractor.relations:
            relation.valid_from = commit_time
            relation.commit_sha_from = commit_sha

        return extractor.entities, extractor.relations
    except SyntaxError as e:
        print(f"  Syntax error in {file_path}: {e}")
        return [], []
    except Exception as e:
        print(f"  Error processing {file_path}: {e}")
        return [], []


def init_database(db_path: Path):
    """Initialize SQLite database with schema."""
    schema_path = db_path.parent / "schema.sql"
    if not schema_path.exists():
        print(f"Schema not found: {schema_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.executescript(schema_path.read_text())
    conn.commit()
    return conn


def store_entities(conn: sqlite3.Connection, entities: List[CodeEntity]):
    """Store entities in SQLite."""
    for e in entities:
        conn.execute("""
            INSERT OR REPLACE INTO entities
            (id, name, entity_type, qualified_name, file_path, line_start, line_end,
             signature, docstring, parent_id, valid_from, valid_until, commit_sha_from,
             commit_sha_until, indexed_at, decorators, is_async, is_property)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            e.get_id(), e.name, e.entity_type, e.qualified_name, e.file_path,
            e.line_start, e.line_end, e.signature, e.docstring, e.parent_id,
            e.valid_from, e.valid_until, e.commit_sha_from, e.commit_sha_until,
            e.indexed_at, json.dumps(e.decorators), e.is_async, e.is_property
        ))
    conn.commit()


def store_relations(conn: sqlite3.Connection, relations: List[CodeRelation]):
    """Store relations in SQLite."""
    for r in relations:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO relations
                (source_id, target_id, target_name, rel_type, valid_from, valid_until,
                 commit_sha_from, line_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.source_id, r.target_id, r.target_name, r.rel_type,
                r.valid_from, r.valid_until, r.commit_sha_from, r.line_number
            ))
        except sqlite3.IntegrityError:
            pass  # Duplicate relation
    conn.commit()


def store_in_chromadb(db_dir: Path, entities: List[CodeEntity]):
    """Store entities in ChromaDB for semantic search."""
    client = chromadb.PersistentClient(
        path=str(db_dir / "chroma_db"),
        settings=Settings(anonymized_telemetry=False),
    )

    try:
        client.delete_collection("code_entities")
    except Exception:
        pass

    collection = client.create_collection(
        name="code_entities",
        metadata={"description": "Bi-temporal code knowledge graph"},
    )

    batch_size = 100
    for i in range(0, len(entities), batch_size):
        batch = entities[i:i + batch_size]
        collection.add(
            ids=[e.get_id() for e in batch],
            documents=[e.to_searchable_text() for e in batch],
            metadatas=[{
                "name": e.name,
                "type": e.entity_type,
                "qualified_name": e.qualified_name,
                "file": e.file_path,
                "line": e.line_start,
                "signature": e.signature or "",
                "valid_from": e.valid_from,
                "decorators": ",".join(e.decorators),
            } for e in batch]
        )


def build_index(source_dir: Path, db_dir: Path, repo_path: Path):
    """Build the bi-temporal code index."""
    start_time = datetime.now()
    print(f"Building bi-temporal code index for {source_dir}...")

    # Initialize databases
    db_path = db_dir / "code_graph.db"
    conn = init_database(db_path)

    # Get current git state
    current_sha, current_time = get_git_info(repo_path)
    print(f"Current commit: {current_sha[:8]} ({current_time})")

    # Store commit
    conn.execute(
        "INSERT OR REPLACE INTO commits (sha, timestamp) VALUES (?, ?)",
        (current_sha, current_time)
    )

    # Extract from all files
    all_entities: List[CodeEntity] = []
    all_relations: List[CodeRelation] = []
    py_files = list(source_dir.rglob("*.py"))

    for py_file in py_files:
        entities, relations = extract_from_file(py_file, repo_path)
        all_entities.extend(entities)
        all_relations.extend(relations)
        if entities:
            print(f"  {py_file.relative_to(source_dir)}: {len(entities)} entities, {len(relations)} relations")

    if not all_entities:
        print("No entities found!")
        return

    # Resolve parent IDs for methods
    entity_map = {e.qualified_name: e.get_id() for e in all_entities}
    for e in all_entities:
        if e.entity_type == "method":
            # Find parent class
            parts = e.qualified_name.rsplit(".", 2)
            if len(parts) >= 2:
                parent_qualified = ".".join(parts[:-1])
                e.parent_id = entity_map.get(parent_qualified)

    # Resolve relation target IDs
    for r in all_relations:
        # Try to find target in our entities
        for qname, eid in entity_map.items():
            if qname.endswith(f".{r.target_name}") or qname == r.target_name:
                r.target_id = eid
                break

    # Store in SQLite
    print(f"\nStoring {len(all_entities)} entities in SQLite...")
    store_entities(conn, all_entities)

    print(f"Storing {len(all_relations)} relations in SQLite...")
    store_relations(conn, all_relations)

    # Store in ChromaDB
    print("Storing in ChromaDB for semantic search...")
    store_in_chromadb(db_dir, all_entities)

    # Record build history
    duration = (datetime.now() - start_time).total_seconds()
    conn.execute("""
        INSERT INTO index_history (rebuilt_at, commit_sha, entity_count, relation_count, duration_seconds)
        VALUES (?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), current_sha, len(all_entities), len(all_relations), duration))
    conn.commit()

    # Print stats
    stats = {
        "classes": sum(1 for e in all_entities if e.entity_type == "class"),
        "methods": sum(1 for e in all_entities if e.entity_type == "method"),
        "functions": sum(1 for e in all_entities if e.entity_type == "function"),
        "total_entities": len(all_entities),
        "relations": {
            "calls": sum(1 for r in all_relations if r.rel_type == "calls"),
            "inherits": sum(1 for r in all_relations if r.rel_type == "inherits"),
            "imports": sum(1 for r in all_relations if r.rel_type == "imports"),
            "uses_type": sum(1 for r in all_relations if r.rel_type == "uses_type"),
            "returns": sum(1 for r in all_relations if r.rel_type == "returns"),
            "raises": sum(1 for r in all_relations if r.rel_type == "raises"),
        },
        "total_relations": len(all_relations),
        "files": len(py_files),
        "commit": current_sha,
        "built_at": datetime.now().isoformat(),
    }

    (db_dir / "stats.json").write_text(json.dumps(stats, indent=2))

    print(f"\n{'='*50}")
    print("Bi-temporal code index built successfully!")
    print(f"{'='*50}")
    print(f"  Entities: {stats['total_entities']}")
    print(f"    - Classes: {stats['classes']}")
    print(f"    - Methods: {stats['methods']}")
    print(f"    - Functions: {stats['functions']}")
    print(f"  Relations: {stats['total_relations']}")
    print(f"    - Calls: {stats['relations']['calls']}")
    print(f"    - Inherits: {stats['relations']['inherits']}")
    print(f"    - Imports: {stats['relations']['imports']}")
    print(f"    - Uses type: {stats['relations']['uses_type']}")
    print(f"  Duration: {duration:.2f}s")

    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build bi-temporal code index")
    parser.add_argument("source_dir", nargs="?", help="Source directory to index")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    db_dir = script_dir

    # Find source directory: CLI arg > src/ > project root
    if args.source_dir:
        source_dir = Path(args.source_dir)
    elif (project_root / "src").exists():
        # Find first package in src/
        src_dirs = [d for d in (project_root / "src").iterdir() if d.is_dir() and not d.name.startswith("_")]
        source_dir = src_dirs[0] if src_dirs else project_root / "src"
    else:
        source_dir = project_root

    if not source_dir.exists():
        print(f"Source directory not found: {source_dir}")
        sys.exit(1)

    print(f"Indexing: {source_dir}")
    build_index(source_dir, db_dir, project_root)
