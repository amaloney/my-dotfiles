#!/usr/bin/env python3
"""Query bi-temporal code knowledge graph.

Supports semantic search (ChromaDB) and temporal/relational queries (SQLite).
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("ChromaDB not installed. Install with: pip install chromadb")
    sys.exit(1)


class CodeGraphQuery:
    """Query interface for bi-temporal code graph."""

    def __init__(self, db_dir: Path):
        self.db_dir = db_dir
        self.db_path = db_dir / "code_graph.db"
        self.conn: Optional[sqlite3.Connection] = None
        self.chroma_client = None
        self.collection = None

    def _get_conn(self) -> sqlite3.Connection:
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def _get_collection(self):
        if self.collection is None:
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.db_dir / "chroma_db"),
                settings=Settings(anonymized_telemetry=False),
            )
            self.collection = self.chroma_client.get_collection("code_entities")
        return self.collection

    def close(self):
        if self.conn:
            self.conn.close()

    # ═══════════════════════════════════════════════════════════════
    # SEMANTIC SEARCH (ChromaDB)
    # ═══════════════════════════════════════════════════════════════

    def search(self, query: str, n_results: int = 5, entity_type: Optional[str] = None) -> List[dict]:
        """Semantic search for code entities."""
        collection = self._get_collection()

        where = {"type": entity_type} if entity_type else None
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
            include=["metadatas", "documents", "distances"]
        )

        entities = []
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i]
            distance = results["distances"][0][i] if results.get("distances") else None
            entities.append({
                "name": meta.get("name"),
                "type": meta.get("type"),
                "qualified_name": meta.get("qualified_name"),
                "file": meta.get("file"),
                "line": meta.get("line"),
                "signature": meta.get("signature"),
                "valid_from": meta.get("valid_from"),
                "distance": distance,
            })
        return entities

    def similar(self, entity_name: str, n_results: int = 5) -> List[dict]:
        """Find entities similar to a given one."""
        collection = self._get_collection()

        # Find the entity first
        results = collection.get(
            where={"name": entity_name},
            include=["documents"]
        )
        if not results["documents"]:
            return []

        # Search for similar
        doc = results["documents"][0]
        return self.search(doc, n_results + 1)[1:]  # Exclude self

    # ═══════════════════════════════════════════════════════════════
    # TEMPORAL QUERIES (SQLite)
    # ═══════════════════════════════════════════════════════════════

    def entities_at_time(self, timestamp: str) -> List[dict]:
        """Get entities that existed at a specific time."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT * FROM entities
            WHERE valid_from <= ?
              AND (valid_until IS NULL OR valid_until > ?)
            ORDER BY qualified_name
        """, (timestamp, timestamp))
        return [dict(row) for row in cursor.fetchall()]

    def changes_since(self, timestamp: str) -> dict:
        """Get entities added/removed since a timestamp."""
        conn = self._get_conn()

        added = conn.execute("""
            SELECT qualified_name, entity_type, file_path, valid_from
            FROM entities
            WHERE valid_from > ?
            ORDER BY valid_from DESC
        """, (timestamp,)).fetchall()

        removed = conn.execute("""
            SELECT qualified_name, entity_type, file_path, valid_until
            FROM entities
            WHERE valid_until IS NOT NULL AND valid_until > ?
            ORDER BY valid_until DESC
        """, (timestamp,)).fetchall()

        return {
            "added": [dict(row) for row in added],
            "removed": [dict(row) for row in removed],
        }

    def entity_history(self, name: str) -> List[dict]:
        """Get history of an entity by name."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT e.*, c.message as commit_message
            FROM entities e
            LEFT JOIN commits c ON e.commit_sha_from = c.sha
            WHERE e.name = ? OR e.qualified_name LIKE ?
            ORDER BY e.valid_from DESC
        """, (name, f"%{name}%"))
        return [dict(row) for row in cursor.fetchall()]

    # ═══════════════════════════════════════════════════════════════
    # RELATIONAL QUERIES (SQLite)
    # ═══════════════════════════════════════════════════════════════

    def callers_of(self, name: str) -> List[dict]:
        """Find all entities that call a given function/method."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT e.name, e.entity_type, e.qualified_name, e.file_path, r.line_number
            FROM relations r
            JOIN entities e ON r.source_id = e.id
            WHERE r.rel_type = 'calls'
              AND r.target_name LIKE ?
              AND r.valid_until IS NULL
            ORDER BY e.file_path, r.line_number
        """, (f"%{name}%",))
        return [dict(row) for row in cursor.fetchall()]

    def calls_from(self, name: str) -> List[dict]:
        """Find all functions/methods called by a given entity."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT DISTINCT r.target_name, r.line_number, e.entity_type as source_type
            FROM relations r
            JOIN entities e ON r.source_id = e.id
            WHERE r.rel_type = 'calls'
              AND (e.name = ? OR e.qualified_name LIKE ?)
              AND r.valid_until IS NULL
            ORDER BY r.line_number
        """, (name, f"%{name}%"))
        return [dict(row) for row in cursor.fetchall()]

    def inheritance_tree(self, class_name: str) -> dict:
        """Get inheritance tree for a class."""
        conn = self._get_conn()

        # Get parents (what this class inherits from)
        parents = conn.execute("""
            SELECT r.target_name
            FROM relations r
            JOIN entities e ON r.source_id = e.id
            WHERE r.rel_type = 'inherits'
              AND (e.name = ? OR e.qualified_name LIKE ?)
              AND r.valid_until IS NULL
        """, (class_name, f"%{class_name}%")).fetchall()

        # Get children (what inherits from this class)
        children = conn.execute("""
            SELECT e.name, e.qualified_name
            FROM relations r
            JOIN entities e ON r.source_id = e.id
            WHERE r.rel_type = 'inherits'
              AND r.target_name LIKE ?
              AND r.valid_until IS NULL
        """, (f"%{class_name}%",)).fetchall()

        return {
            "class": class_name,
            "inherits_from": [row[0] for row in parents],
            "inherited_by": [{"name": row[0], "qualified_name": row[1]} for row in children],
        }

    def dependencies_of(self, name: str) -> dict:
        """Get all dependencies of an entity (calls, imports, uses_type)."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT r.rel_type, r.target_name, COUNT(*) as count
            FROM relations r
            JOIN entities e ON r.source_id = e.id
            WHERE (e.name = ? OR e.qualified_name LIKE ?)
              AND r.valid_until IS NULL
            GROUP BY r.rel_type, r.target_name
            ORDER BY r.rel_type, count DESC
        """, (name, f"%{name}%"))

        deps = {"calls": [], "imports": [], "uses_type": [], "inherits": [], "raises": []}
        for row in cursor.fetchall():
            rel_type = row[0]
            if rel_type in deps:
                deps[rel_type].append({"name": row[1], "count": row[2]})
        return deps

    def impact_of_change(self, name: str) -> dict:
        """Analyze impact if an entity is changed/removed."""
        conn = self._get_conn()

        # Direct callers
        callers = self.callers_of(name)

        # Classes that inherit
        inheritors = conn.execute("""
            SELECT e.name, e.qualified_name, e.file_path
            FROM relations r
            JOIN entities e ON r.source_id = e.id
            WHERE r.rel_type = 'inherits'
              AND r.target_name LIKE ?
              AND r.valid_until IS NULL
        """, (f"%{name}%",)).fetchall()

        # Types that reference
        type_users = conn.execute("""
            SELECT e.name, e.qualified_name, e.file_path
            FROM relations r
            JOIN entities e ON r.source_id = e.id
            WHERE (r.rel_type = 'uses_type' OR r.rel_type = 'returns')
              AND r.target_name LIKE ?
              AND r.valid_until IS NULL
        """, (f"%{name}%",)).fetchall()

        return {
            "entity": name,
            "direct_callers": len(callers),
            "callers": callers[:10],  # Limit
            "inheritors": [dict(row) for row in inheritors],
            "type_users": [dict(row) for row in type_users],
            "total_impact": len(callers) + len(inheritors) + len(type_users),
        }

    # ═══════════════════════════════════════════════════════════════
    # FIX LEARNING QUERIES
    # ═══════════════════════════════════════════════════════════════

    def record_fix_attempt(self, package: str, error_type: str, fix_action: str,
                          error_message: str = "", fix_details: str = "",
                          file_path: Optional[str] = None, commit_sha: Optional[str] = None) -> int:
        """Record a fix attempt for learning."""
        conn = self._get_conn()
        cursor = conn.execute("""
            INSERT INTO fix_attempts
            (package, error_type, error_message, fix_action, fix_details, file_path,
             attempted_at, commit_sha, outcome)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (package, error_type, error_message, fix_action, fix_details, file_path,
              datetime.now().isoformat(), commit_sha))
        conn.commit()
        return cursor.lastrowid

    def update_fix_outcome(self, fix_id: int, outcome: str, notes: str = ""):
        """Update the outcome of a fix attempt."""
        conn = self._get_conn()
        conn.execute("""
            UPDATE fix_attempts
            SET outcome = ?, notes = ?, completed_at = ?
            WHERE id = ?
        """, (outcome, notes, datetime.now().isoformat(), fix_id))
        conn.commit()

    def successful_fixes_for(self, error_type: str) -> List[dict]:
        """Get successful fixes for an error type."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT fix_action, COUNT(*) as count,
                   GROUP_CONCAT(DISTINCT package) as packages
            FROM fix_attempts
            WHERE error_type = ? AND outcome = 'success'
            GROUP BY fix_action
            ORDER BY count DESC
        """, (error_type,))
        return [dict(row) for row in cursor.fetchall()]

    def fix_history_for_package(self, package: str) -> List[dict]:
        """Get fix attempt history for a package."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT * FROM fix_attempts
            WHERE package = ?
            ORDER BY attempted_at DESC
        """, (package,))
        return [dict(row) for row in cursor.fetchall()]

    def fix_success_rates(self) -> List[dict]:
        """Get success rates by error type and action."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM fix_success_rates")
        return [dict(row) for row in cursor.fetchall()]

    # ═══════════════════════════════════════════════════════════════
    # STATS AND LISTING
    # ═══════════════════════════════════════════════════════════════

    def stats(self) -> dict:
        """Get index statistics."""
        stats_path = self.db_dir / "stats.json"
        if stats_path.exists():
            return json.loads(stats_path.read_text())
        return {}

    def list_classes(self) -> List[dict]:
        """List all current classes."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT name, qualified_name, file_path, line_start, signature
            FROM current_entities
            WHERE entity_type = 'class'
            ORDER BY file_path, line_start
        """)
        return [dict(row) for row in cursor.fetchall()]

    def list_methods(self, class_name: Optional[str] = None) -> List[dict]:
        """List methods, optionally filtered by class."""
        conn = self._get_conn()
        if class_name:
            cursor = conn.execute("""
                SELECT e.name, e.qualified_name, e.signature, e.file_path, e.line_start
                FROM current_entities e
                WHERE e.entity_type = 'method'
                  AND e.qualified_name LIKE ?
                ORDER BY e.line_start
            """, (f"%.{class_name}.%",))
        else:
            cursor = conn.execute("""
                SELECT name, qualified_name, signature, file_path, line_start
                FROM current_entities
                WHERE entity_type = 'method'
                ORDER BY file_path, line_start
            """)
        return [dict(row) for row in cursor.fetchall()]

    def list_functions(self) -> List[dict]:
        """List all current functions."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT name, qualified_name, signature, file_path, line_start
            FROM current_entities
            WHERE entity_type = 'function'
            ORDER BY file_path, line_start
        """)
        return [dict(row) for row in cursor.fetchall()]

    def show(self, name: str) -> Optional[dict]:
        """Show detailed info about an entity."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT * FROM entities
            WHERE name = ? OR qualified_name LIKE ?
            ORDER BY valid_from DESC
            LIMIT 1
        """, (name, f"%{name}%"))
        row = cursor.fetchone()
        if row:
            entity = dict(row)
            # Add relations
            entity["calls"] = self.calls_from(name)[:20]
            entity["called_by"] = self.callers_of(name)[:20]
            return entity
        return None


def main():
    parser = argparse.ArgumentParser(
        prog="query_temporal",
        description="Query bi-temporal code knowledge graph"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Search
    p = subparsers.add_parser("search", help="Semantic search for code")
    p.add_argument("query", help="Search query")
    p.add_argument("-n", "--results", type=int, default=5)
    p.add_argument("-t", "--type", choices=["class", "method", "function"])

    # Similar
    p = subparsers.add_parser("similar", help="Find similar entities")
    p.add_argument("name", help="Entity name")
    p.add_argument("-n", "--results", type=int, default=5)

    # Callers
    p = subparsers.add_parser("callers", help="Find callers of a function/method")
    p.add_argument("name", help="Function/method name")

    # Calls
    p = subparsers.add_parser("calls", help="Find what a function/method calls")
    p.add_argument("name", help="Function/method name")

    # Inheritance
    p = subparsers.add_parser("inheritance", help="Show inheritance tree")
    p.add_argument("class_name", help="Class name")

    # Dependencies
    p = subparsers.add_parser("deps", help="Show dependencies of an entity")
    p.add_argument("name", help="Entity name")

    # Impact
    p = subparsers.add_parser("impact", help="Analyze change impact")
    p.add_argument("name", help="Entity name")

    # Changes
    p = subparsers.add_parser("changes", help="Show changes since a date")
    p.add_argument("since", help="ISO timestamp or days ago (e.g., '7d')")

    # History
    p = subparsers.add_parser("history", help="Show entity history")
    p.add_argument("name", help="Entity name")

    # List
    subparsers.add_parser("list-classes", help="List all classes")
    p = subparsers.add_parser("list-methods", help="List methods")
    p.add_argument("class_name", nargs="?", help="Filter by class")
    subparsers.add_parser("list-functions", help="List all functions")

    # Show
    p = subparsers.add_parser("show", help="Show entity details")
    p.add_argument("name", help="Entity name")

    # Stats
    subparsers.add_parser("stats", help="Show index statistics")

    # Fix learning
    p = subparsers.add_parser("fix-rates", help="Show fix success rates")
    p = subparsers.add_parser("fix-history", help="Show fix history for package")
    p.add_argument("package", help="Package name")

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    query = CodeGraphQuery(script_dir)

    try:
        if args.command == "search":
            results = query.search(args.query, args.results, args.type)
            for r in results:
                dist = f" (dist: {r['distance']:.3f})" if r.get('distance') else ""
                print(f"{r['type']:8} {r['qualified_name']}{dist}")
                if r['signature']:
                    print(f"         {r['signature']}")

        elif args.command == "similar":
            results = query.similar(args.name, args.results)
            for r in results:
                print(f"{r['type']:8} {r['qualified_name']}")

        elif args.command == "callers":
            results = query.callers_of(args.name)
            print(f"Callers of '{args.name}':")
            for r in results:
                print(f"  {r['qualified_name']}:{r['line_number']}")

        elif args.command == "calls":
            results = query.calls_from(args.name)
            print(f"Called by '{args.name}':")
            for r in results:
                print(f"  {r['target_name']} (line {r['line_number']})")

        elif args.command == "inheritance":
            tree = query.inheritance_tree(args.class_name)
            print(f"Inheritance tree for '{tree['class']}':")
            if tree['inherits_from']:
                print(f"  Inherits from: {', '.join(tree['inherits_from'])}")
            if tree['inherited_by']:
                print(f"  Inherited by:")
                for c in tree['inherited_by']:
                    print(f"    - {c['qualified_name']}")

        elif args.command == "deps":
            deps = query.dependencies_of(args.name)
            print(f"Dependencies of '{args.name}':")
            for rel_type, items in deps.items():
                if items:
                    print(f"  {rel_type}:")
                    for item in items[:10]:
                        print(f"    - {item['name']} ({item['count']}x)")

        elif args.command == "impact":
            impact = query.impact_of_change(args.name)
            print(f"Impact analysis for '{args.name}':")
            print(f"  Total impact: {impact['total_impact']} entities")
            print(f"  Direct callers: {impact['direct_callers']}")
            if impact['inheritors']:
                print(f"  Inheritors: {len(impact['inheritors'])}")
            if impact['type_users']:
                print(f"  Type users: {len(impact['type_users'])}")

        elif args.command == "changes":
            since = args.since
            if since.endswith("d"):
                from datetime import timedelta
                days = int(since[:-1])
                since = (datetime.now() - timedelta(days=days)).isoformat()

            changes = query.changes_since(since)
            print(f"Changes since {since}:")
            if changes['added']:
                print(f"  Added ({len(changes['added'])}):")
                for e in changes['added'][:10]:
                    print(f"    + {e['qualified_name']}")
            if changes['removed']:
                print(f"  Removed ({len(changes['removed'])}):")
                for e in changes['removed'][:10]:
                    print(f"    - {e['qualified_name']}")

        elif args.command == "history":
            history = query.entity_history(args.name)
            print(f"History for '{args.name}':")
            for h in history:
                status = "removed" if h.get('valid_until') else "current"
                print(f"  {h['valid_from'][:10]} [{status}] {h['qualified_name']}")

        elif args.command == "list-classes":
            classes = query.list_classes()
            current_file = None
            for c in classes:
                if c['file_path'] != current_file:
                    current_file = c['file_path']
                    print(f"\n{current_file}:")
                print(f"  {c['name']} (line {c['line_start']})")

        elif args.command == "list-methods":
            methods = query.list_methods(getattr(args, 'class_name', None))
            for m in methods:
                print(f"{m['qualified_name']}")

        elif args.command == "list-functions":
            functions = query.list_functions()
            for f in functions:
                print(f"{f['qualified_name']}")

        elif args.command == "show":
            entity = query.show(args.name)
            if entity:
                print(json.dumps(entity, indent=2, default=str))
            else:
                print(f"Entity '{args.name}' not found")

        elif args.command == "stats":
            stats = query.stats()
            print(json.dumps(stats, indent=2))

        elif args.command == "fix-rates":
            rates = query.fix_success_rates()
            print("Fix success rates:")
            for r in rates:
                print(f"  {r['error_type']} + {r['fix_action']}: {r['success_rate']}% ({r['successes']}/{r['total']})")

        elif args.command == "fix-history":
            history = query.fix_history_for_package(args.package)
            print(f"Fix history for '{args.package}':")
            for h in history:
                print(f"  {h['attempted_at'][:10]} {h['error_type']} -> {h['fix_action']}: {h['outcome']}")

    finally:
        query.close()


if __name__ == "__main__":
    main()
