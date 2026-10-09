#!/usr/bin/env python3
"""Extract code entities and relations from Rust source via tree-sitter.

Language-neutral output consumed by build_index.py and build_index_temporal.py,
which map RustItem / RustRelation onto their own CodeEntity / CodeRelation types.

Mapping:
    struct / enum / trait / union   -> "class"
    fn inside impl or trait         -> "method" (parent = impl self type / trait name)
    free fn                         -> "function"
    /// doc comments                -> docstring
    #[attributes]                   -> decorators
    impl Trait for Type             -> relation "inherits" (Type -> Trait)
    use declarations (in fn bodies) -> relation "imports" (module-level imports skipped, as in the Python indexer)
    call expressions                -> relation "calls"

Requires the optional `tree_sitter` + `tree_sitter_rust` packages; RUST_AVAILABLE
is False when they are missing so callers can skip .rs files with one warning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tree_sitter import Node

try:
    import tree_sitter_rust
    from tree_sitter import Language, Parser

    RUST_PARSER: Parser | None = Parser(Language(tree_sitter_rust.language()))
except (ImportError, TypeError, ValueError):  # missing or API/ABI-incompatible tree-sitter
    RUST_PARSER = None

RUST_AVAILABLE = RUST_PARSER is not None
RUST_INSTALL_HINT = "pixi add --feature dev tree_sitter tree-sitter-rust"

# Shared with build_index.py / build_index_temporal.py
CARGO_MANIFEST = "Cargo.toml"
EXCLUDE_DIRS_RUST = frozenset({"target"})

KINDS_CLASS = frozenset({"struct_item", "enum_item", "trait_item", "union_item"})
KINDS_FUNCTION = frozenset({"function_item", "function_signature_item"})
KINDS_DOC_SIBLING = frozenset({"line_comment", "block_comment", "attribute_item"})
KINDS_TYPE_BOUND = frozenset({"type_identifier", "scoped_type_identifier", "generic_type"})
KINDS_PATH_CALLEE = frozenset({"scoped_identifier", "field_expression"})
# `src/lib.rs`, `src/main.rs`, `foo/mod.rs` name their parent module, not a child
STEMS_MODULE_ROOT = frozenset({"lib", "main", "mod"})


@dataclass
class RustRelation:
    """Relation from an entity to a named target (resolved to ids by the caller).

    `rel_type` mirrors the `relations.rel_type` column of the code-index schema.
    """

    target_name: str
    rel_type: str
    line_number: int


@dataclass
class RustItem:
    """One extracted Rust entity."""

    name: str
    entity_type: str
    qualified_name: str
    line_start: int
    line_end: int
    signature: str
    docstring: str | None
    parent_class: str | None
    decorators: list[str]
    source_code: str
    is_async: bool = False
    relations: list[RustRelation] = field(default_factory=list)


def node_text(node: Node) -> str:
    """Decode a node's source bytes.

    Args:
        node: Any tree-sitter node.

    Returns:
        The node's source text; empty when the node carries no text.
    """
    return node.text.decode("utf-8", errors="replace") if node.text else ""


def line_of(node: Node) -> int:
    """1-based start line of a node (tree-sitter rows are 0-based).

    Args:
        node: Any tree-sitter node.

    Returns:
        The 1-based line number.
    """
    return node.start_point[0] + 1


def doc_and_attributes(node: Node) -> tuple[str | None, list[str]]:
    """Collect `///` docs and `#[...]` attributes from the siblings directly above an item.

    Args:
        node: An item node (fn, struct, enum, trait, ...).

    Returns:
        The joined doc comment (None when absent) and the attribute bodies, e.g. `derive(Debug)`.
    """
    doc_lines: list[str] = []
    attributes: list[str] = []
    sibling = node.prev_named_sibling
    while sibling is not None and sibling.type in KINDS_DOC_SIBLING:
        text = node_text(sibling)
        if sibling.type == "attribute_item":
            attributes.insert(0, text.removeprefix("#[").removesuffix("]").strip())
        elif text.startswith("///") and not text.startswith("////"):
            doc_lines.insert(0, text.removeprefix("///").strip())
        elif text.startswith("/**"):
            doc_lines.insert(0, text.removeprefix("/**").removesuffix("*/").strip())
        else:
            break
        sibling = sibling.prev_named_sibling
    docstring = "\n".join(doc_lines) if doc_lines else None
    return docstring, attributes


def signature_of(node: Node) -> str:
    """Item header up to (not including) its body block, whitespace-collapsed.

    Args:
        node: An item node.

    Returns:
        e.g. `pub fn parse(text: &str) -> Result<Self, ParseError>`.
    """
    body = node.child_by_field_name("body")
    end = body.start_byte if body is not None and body.type != "ordered_field_declaration_list" else node.end_byte
    header = node.text[: end - node.start_byte].decode("utf-8", errors="replace") if node.text else ""
    return " ".join(header.split()).rstrip(" {;")


def type_name(node: Node | None) -> str | None:
    """Bare type name: `Vec<T>` -> `Vec`, `crate::a::Foo` -> `Foo`.

    Args:
        node: A type node, or None when the parent has no such field.

    Returns:
        The final path segment without generics; None when `node` is None.
    """
    name = None
    if node is None:
        name = None
    elif node.type == "generic_type":
        name = type_name(node.child_by_field_name("type"))
    elif node.type == "scoped_type_identifier":
        name = type_name(node.child_by_field_name("name"))
    else:
        name = node_text(node)
    return name


def call_target(node: Node) -> str | None:
    """Callee name of a call expression: `a.b()` -> `b`, `x::y()` -> `y`, `f::<T>()` -> `f`.

    Args:
        node: A `call_expression` node.

    Returns:
        The callee's final name segment; None for callees with no name (closures, indexing).
    """
    callee = node.child_by_field_name("function")
    if callee is not None and callee.type == "generic_function":
        callee = callee.child_by_field_name("function")

    name_node = None
    if callee is None:
        name_node = None
    elif callee.type == "identifier":
        name_node = callee
    elif callee.type in KINDS_PATH_CALLEE:
        name_node = callee.child_by_field_name("name") or callee.child_by_field_name("field")
    return node_text(name_node) if name_node is not None else None


def collect_body_relations(node: Node) -> list[RustRelation]:
    """Calls and local `use` declarations inside a function body.

    Args:
        node: A function item node.

    Returns:
        One relation per call expression and per `use` declaration found in the subtree.
    """
    relations: list[RustRelation] = []
    stack = [node]
    while stack:
        current = stack.pop()
        if current.type == "call_expression":
            target = call_target(current)
            if target:
                relations.append(RustRelation(target_name=target, rel_type="calls", line_number=line_of(current)))
        elif current.type == "use_declaration":
            argument = current.child_by_field_name("argument")
            if argument is not None:
                use_path = " ".join(node_text(argument).split())
                relations.append(RustRelation(target_name=use_path, rel_type="imports", line_number=line_of(current)))
        stack.extend(current.named_children)
    return relations


class RustExtractor:
    """Walk a parsed Rust file and collect items."""

    def __init__(self, module_name: str) -> None:
        self.module_name = module_name
        self.items: list[RustItem] = []
        # (self type, trait, line) from `impl Trait for Type`, attached to Type after the walk
        self.trait_impls: list[tuple[str, str, int]] = []

    def qualify(self, scope: list[str], name: str) -> str:
        """Dotted qualified name, matching the Python indexer's `module.Class.method` shape.

        Args:
            scope: Enclosing inline modules / impl or trait types, outermost first.
            name: The item's own name.

        Returns:
            e.g. `net.http.Client.send`; the crate root module contributes no segment.
        """
        segments = [self.module_name, *scope, name] if self.module_name else [*scope, name]
        return ".".join(segments)

    def walk(self, container: Node, scope: list[str], parent_class: str | None) -> None:
        """Extract every item directly inside `container`, recursing into inline modules, impls and traits.

        Args:
            container: A `source_file`, `declaration_list`, or module body node.
            scope: Enclosing names for qualification.
            parent_class: Impl self type or trait name when walking their bodies; makes fns methods.
        """
        for child in container.named_children:
            if child.type in KINDS_FUNCTION:
                self.add_function(child, scope=scope, parent_class=parent_class)
            elif child.type in KINDS_CLASS:
                self.add_class(child, scope=scope)
            elif child.type == "impl_item":
                self.add_impl(child, scope=scope)
            elif child.type == "mod_item":
                body = child.child_by_field_name("body")
                name_node = child.child_by_field_name("name")
                if body is not None and name_node is not None:
                    self.walk(body, scope=[*scope, node_text(name_node)], parent_class=None)

    def add_function(self, node: Node, scope: list[str], parent_class: str | None) -> None:
        """Record a fn as a method (inside impl/trait) or free function.

        Args:
            node: A `function_item` or `function_signature_item` node.
            scope: Enclosing names for qualification.
            parent_class: Owning impl type / trait, or None for free fns.
        """
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            docstring, attributes = doc_and_attributes(node)
            signature = signature_of(node)
            self.items.append(
                RustItem(
                    name=node_text(name_node),
                    entity_type="method" if parent_class else "function",
                    qualified_name=self.qualify(scope, node_text(name_node)),
                    line_start=line_of(node),
                    line_end=node.end_point[0] + 1,
                    signature=signature,
                    docstring=docstring,
                    parent_class=parent_class,
                    decorators=attributes,
                    source_code=node_text(node),
                    is_async="async" in signature.split(" fn ", 1)[0].split(),
                    relations=collect_body_relations(node),
                )
            )

    def add_class(self, node: Node, scope: list[str]) -> None:
        """Record a struct/enum/trait/union; traits also record supertraits and their method signatures.

        Args:
            node: A struct/enum/trait/union item node.
            scope: Enclosing names for qualification.
        """
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            name = node_text(name_node)
            docstring, attributes = doc_and_attributes(node)
            bounds = node.child_by_field_name("bounds")
            # Supertraits: `trait Reader: Read + Debug`
            supertraits = (
                [
                    RustRelation(
                        target_name=type_name(bound) or node_text(bound),
                        rel_type="inherits",
                        line_number=line_of(node),
                    )
                    for bound in bounds.named_children
                    if bound.type in KINDS_TYPE_BOUND
                ]
                if node.type == "trait_item" and bounds is not None
                else []
            )
            self.items.append(
                RustItem(
                    name=name,
                    entity_type="class",
                    qualified_name=self.qualify(scope, name),
                    line_start=line_of(node),
                    line_end=node.end_point[0] + 1,
                    signature=signature_of(node),
                    docstring=docstring,
                    parent_class=None,
                    decorators=attributes,
                    source_code=node_text(node),
                    relations=supertraits,
                )
            )
            body = node.child_by_field_name("body")
            if node.type == "trait_item" and body is not None:
                self.walk(body, scope=[*scope, name], parent_class=name)

    def add_impl(self, node: Node, scope: list[str]) -> None:
        """Walk an impl block's fns as methods of its self type; remember `impl Trait for Type`.

        Args:
            node: An `impl_item` node.
            scope: Enclosing names for qualification.
        """
        self_type = type_name(node.child_by_field_name("type"))
        trait = type_name(node.child_by_field_name("trait"))
        body = node.child_by_field_name("body")
        if self_type is not None and body is not None:
            if trait:
                self.trait_impls.append((self_type, trait, line_of(node)))
            self.walk(body, scope=[*scope, self_type], parent_class=self_type)


def module_name_for(file_path: Path, crate_root: Path) -> str:
    """Dotted module path of a source file within its crate.

    Args:
        file_path: The `.rs` file.
        crate_root: Directory holding the crate's Cargo.toml.

    Returns:
        `src/net/http.rs` -> `net.http`; `src/lib.rs`, `src/main.rs` -> ``; `src/net/mod.rs` -> `net`.
    """
    try:
        relative = file_path.relative_to(crate_root / "src")
    except ValueError:
        try:
            relative = file_path.relative_to(crate_root)
        except ValueError:
            relative = Path(file_path.name)
    parts = list(relative.with_suffix("").parts)
    if parts and parts[-1] in STEMS_MODULE_ROOT:
        parts = parts[:-1]
    return ".".join(parts)


def find_crate_root(file_path: Path, repo_root: Path) -> Path:
    """Nearest ancestor holding Cargo.toml (workspace members have their own src/).

    Args:
        file_path: The `.rs` file.
        repo_root: Upper bound for the search.

    Returns:
        The crate directory, or `repo_root` when no manifest is found below it.
    """
    crate_root = repo_root
    for ancestor in file_path.parents:
        if (ancestor / CARGO_MANIFEST).is_file():
            crate_root = ancestor
            break
        if ancestor == repo_root:
            break
    return crate_root


def extract_rust(file_path: Path, repo_root: Path) -> list[RustItem]:
    """Parse one .rs file into items, each carrying its own relations.

    Args:
        file_path: The `.rs` file to parse.
        repo_root: Repository root; bounds the crate-root search.

    Returns:
        Every struct/enum/trait/union, method and free fn in the file.

    Raises:
        RuntimeError: tree-sitter-rust is not installed.
    """
    if RUST_PARSER is None:
        raise RuntimeError(f"tree-sitter-rust not installed: {RUST_INSTALL_HINT}")
    tree = RUST_PARSER.parse(file_path.read_bytes())
    extractor = RustExtractor(module_name=module_name_for(file_path, find_crate_root(file_path, repo_root)))
    extractor.walk(tree.root_node, scope=[], parent_class=None)

    # `impl Trait for Type` -> inherits edge on Type, when Type is defined in this file
    items_by_name = {item.name: item for item in extractor.items if item.entity_type == "class"}
    for self_type, trait, line_number in extractor.trait_impls:
        owner = items_by_name.get(self_type)
        if owner is not None:
            owner.relations.append(RustRelation(target_name=trait, rel_type="inherits", line_number=line_number))
    return extractor.items


if __name__ == "__main__":
    import sys

    for argument in sys.argv[1:]:
        for item in extract_rust(Path(argument).resolve(), Path.cwd().resolve()):
            print(f"{item.entity_type:8} {item.qualified_name:40} L{item.line_start}  {item.signature}")
            for relation in item.relations:
                print(f"           {relation.rel_type:8} {relation.target_name}")
