import sqlite3
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from export_graph import build_graph  # noqa: E402


def test_graph_template_draws_edges_toward_their_targets() -> None:
    template = (SCRIPTS / "viz_template.html").read_text()

    assert "function drawArrow(source, target)" in template
    assert "drawArrow(e.source, e.target);" in template


def test_graph_template_exposes_module_objects_and_hypergraph_views() -> None:
    template = (SCRIPTS / "viz_template.html").read_text()

    assert '<option value="module">Module</option>' in template
    assert '<option value="objects">Objects</option>' in template
    assert '<option value="hypergraph">Hypergraph</option>' in template
    assert "GRAPH_DATA.hyperedges" in template


def test_module_dependency_is_outgoing_to_its_dependency(tmp_path: Path) -> None:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE current_entities (
            id TEXT,
            name TEXT,
            entity_type TEXT,
            file_path TEXT,
            line_start INTEGER,
            line_end INTEGER,
            signature TEXT
        );
        CREATE TABLE current_relations (
            source_id TEXT,
            target_id TEXT,
            target_name TEXT,
            rel_type TEXT
        );
        """
    )
    conn.executemany(
        "INSERT INTO current_entities VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("api", "handle", "function", str(tmp_path / "pkg/api.py"), 1, 5, ""),
            ("core", "helper", "function", str(tmp_path / "pkg/core.py"), 1, 3, ""),
        ],
    )
    conn.execute(
        "INSERT INTO current_relations VALUES (?, ?, ?, ?)",
        ("api", None, "pkg.core.helper", "imports"),
    )

    graph = build_graph(conn, tmp_path)

    assert graph["module"]["edges"] == [
        {"source": "pkg/api.py", "target": "pkg/core.py", "kind": "imports", "weight": 1}
    ]
    assert not any(
        edge["source"] == "pkg/core.py" and edge["target"] == "pkg/api.py" for edge in graph["module"]["edges"]
    )
    assert graph["stats"]["modules"] == 2
    assert graph["stats"]["objects"] == 2


def test_hyperedge_links_object_to_modules_that_define_and_use_it(tmp_path: Path) -> None:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE current_entities (
            id TEXT,
            name TEXT,
            entity_type TEXT,
            file_path TEXT,
            line_start INTEGER,
            line_end INTEGER,
            signature TEXT
        );
        CREATE TABLE current_relations (
            source_id TEXT,
            target_id TEXT,
            target_name TEXT,
            rel_type TEXT
        );
        """
    )
    conn.executemany(
        "INSERT INTO current_entities VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("api", "handle", "function", str(tmp_path / "pkg/api.py"), 1, 5, ""),
            ("core", "helper", "function", str(tmp_path / "pkg/core.py"), 1, 3, ""),
        ],
    )
    conn.execute(
        "INSERT INTO current_relations VALUES (?, ?, ?, ?)",
        ("api", "core", None, "calls"),
    )

    graph = build_graph(conn, tmp_path)
    hyperedge = next(h for h in graph["hyperedges"] if h["id"] == "core")

    assert hyperedge["defined_in"] == "pkg/core.py"
    assert hyperedge["used_in"] == ["pkg/api.py"]
    assert hyperedge["modules"] == ["pkg/core.py", "pkg/api.py"]
    assert graph["stats"]["hyperedges"] == 2
