"""Tests for extract_rust: tree-sitter extraction of Rust items for the code index."""

import sys
from pathlib import Path

import pytest

pytest.importorskip("tree_sitter_rust")

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from extract_rust import RustItem, extract_rust, module_name_for  # noqa: E402

LIB_RS = '''\
//! Fixture crate.
pub mod net;

/// A parsed header.
#[derive(Debug, Clone)]
pub struct Header {
    pub version: u32,
}

impl Header {
    /// Parse `v=N`.
    pub fn parse(text: &str) -> Option<Self> {
        let digits = text.strip_prefix("v=")?;
        Some(Self { version: digits.parse().ok()? })
    }
}

impl std::fmt::Display for Header {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "v={}", self.version)
    }
}

pub trait Codec: std::fmt::Debug {
    fn encode(&self) -> String;
}

pub async fn fetch_all() -> usize {
    helper(3)
}

fn helper(count: usize) -> usize {
    use std::cmp::max;
    max(count, 1)
}
'''


@pytest.fixture
def crate(tmp_path: Path) -> Path:
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "fixture"\nversion = "0.1.0"\nedition = "2021"\n')
    (tmp_path / "src" / "net").mkdir(parents=True)
    (tmp_path / "src" / "lib.rs").write_text(LIB_RS)
    (tmp_path / "src" / "net" / "mod.rs").write_text("pub mod http;\n")
    (tmp_path / "src" / "net" / "http.rs").write_text("/// Send.\npub fn send(url: &str) -> usize { url.len() }\n")
    return tmp_path


def items_by_qualified_name(crate: Path, relative: str) -> dict[str, RustItem]:
    """Extract one fixture file, keyed for direct lookup by qualified name.

    Args:
        crate: Fixture crate root.
        relative: Source path relative to the crate root.

    Returns:
        Extracted items keyed by `qualified_name`.
    """
    return {item.qualified_name: item for item in extract_rust(crate / relative, crate)}


def test_struct_is_class_with_doc_and_attributes(crate: Path) -> None:
    header = items_by_qualified_name(crate, "src/lib.rs")["Header"]
    assert header.entity_type == "class"
    assert header.docstring == "A parsed header."
    assert header.decorators == ["derive(Debug, Clone)"]
    assert header.signature == "pub struct Header"


def test_impl_fn_is_method_with_parent(crate: Path) -> None:
    items = items_by_qualified_name(crate, "src/lib.rs")
    parse = items["Header.parse"]
    assert parse.entity_type == "method"
    assert parse.parent_class == "Header"
    assert parse.docstring == "Parse `v=N`."
    assert parse.signature == "pub fn parse(text: &str) -> Option<Self>"
    assert items["Header.fmt"].parent_class == "Header"


def test_trait_impl_and_supertrait_become_inherits(crate: Path) -> None:
    items = items_by_qualified_name(crate, "src/lib.rs")
    header_relations = [(relation.rel_type, relation.target_name) for relation in items["Header"].relations]
    codec_relations = [(relation.rel_type, relation.target_name) for relation in items["Codec"].relations]
    assert header_relations == [("inherits", "Display")]
    assert ("inherits", "Debug") in codec_relations
    assert items["Codec.encode"].entity_type == "method"


def test_free_fn_calls_imports_and_async(crate: Path) -> None:
    items = items_by_qualified_name(crate, "src/lib.rs")
    assert items["fetch_all"].entity_type == "function"
    assert items["fetch_all"].is_async
    fetch_relations = [(relation.rel_type, relation.target_name) for relation in items["fetch_all"].relations]
    helper_relations = {(relation.rel_type, relation.target_name) for relation in items["helper"].relations}
    assert ("calls", "helper") in fetch_relations
    assert {("calls", "max"), ("imports", "std::cmp::max")} <= helper_relations
    assert not items["helper"].is_async


def test_nested_module_qualified_name(crate: Path) -> None:
    assert list(items_by_qualified_name(crate, "src/net/http.rs")) == ["net.http.send"]
    assert extract_rust(crate / "src" / "net" / "mod.rs", crate) == []


@pytest.mark.parametrize(
    ("relative", "expected"),
    [("src/lib.rs", ""), ("src/main.rs", ""), ("src/net/mod.rs", "net"), ("src/net/http.rs", "net.http")],
)
def test_module_name_for(tmp_path: Path, relative: str, expected: str) -> None:
    assert module_name_for(tmp_path / relative, tmp_path) == expected
