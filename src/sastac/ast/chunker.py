from dataclasses import dataclass, asdict
from typing import List, Optional

from tree_sitter import Node, Tree

from sastac.ast.parser import parse_code
from sastac.ast.parser import TOP_LEVEL_NODE_TYPES


# -----------------------------
# Data Model
# -----------------------------

@dataclass
class CodeChunk:
    language: str
    node_type: str
    name: Optional[str]
    parent_name: Optional[str]
    depth: int

    start_byte: int
    end_byte: int
    start_line: int
    end_line: int

    signature: str
    body: str
    docstring: Optional[str]

    class_name: Optional[str] = None
    class_annotations: list[str] | None = None
    method_annotations: list[str] | None = None
    package: Optional[str] = None

    def to_metadata(self):
        return asdict(self)


# -----------------------------
# Utilities
# -----------------------------

def _node_text(node: Node, source: str) -> str:
    return source[node.start_byte : node.end_byte]


def _extract_identifier(node: Node) -> Optional[str]:
    """
    Attempt to extract identifier/name across grammars.
    """
    for child in node.children:
        if child.type in {"identifier", "name"}:
            return child.text.decode("utf-8")
    return None


def _extract_docstring(node: Node, language: str, source: str) -> Optional[str]:
    """
    Very lightweight docstring extraction.
    Python: first string literal inside block.
    Others: left for extension.
    """
    if language == "python":
        for child in node.children:
            if child.type == "block":
                for stmt in child.children:
                    if stmt.type == "expression_statement":
                        for expr_child in stmt.children:
                            if expr_child.type == "string":
                                return _node_text(expr_child, source)
    return None


def _extract_annotations(node: Node, source: str) -> list[str]:
    anns = []

    for child in node.children:
        # Java tree-sitter uses these
        if child.type in {"annotation", "marker_annotation"}:
            anns.append(source[child.start_byte:child.end_byte])

    return anns


def _extract_signature(node: Node, source: str) -> str:
    """
    Extract header portion (everything before block/body if present).
    """
    for child in node.children:
        if child.type in {"block", "statement_block"}:
            return source[node.start_byte : child.start_byte].strip()
    return _node_text(node, source)


def _extract_package(root: Node, source: str) -> Optional[str]:
    for child in root.children:
        if child.type == "package_declaration":
            text = source[child.start_byte:child.end_byte]
            return text.replace("package", "").replace(";", "").strip()
    return None


# -----------------------------
# Recursive Traversal
# -----------------------------

def _collect_nodes_recursive(
    node: Node,
    language: str,
    source: str,
    allowed_types: set,
    parent_name: Optional[str] = None,
    depth: int = 0,
    current_class=None,
    class_annotations=None,
    package=None,
) -> List[CodeChunk]:

    chunks: List[CodeChunk] = []

    current_name = parent_name

    if node.type in allowed_types:
        name = _extract_identifier(node)

        current_class = None
        class_annotations = []
        if node.type == "class_declaration":
            current_class = _extract_identifier(node)
            class_annotations = _extract_annotations(node, source)
        
        method_annotations = None
        if node.type in {"method_declaration", "constructor_declaration"}:
            method_annotations = _extract_annotations(node, source)

        chunk = CodeChunk(
            language=language,
            node_type=node.type,
            name=name,
            parent_name=parent_name,
            depth=depth,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            start_line=node.start_point[0],
            end_line=node.end_point[0],
            signature=_extract_signature(node, source),
            body=_node_text(node, source),
            docstring=_extract_docstring(node, language, source),
            class_name=current_class,
            class_annotations=class_annotations,
            method_annotations=method_annotations,
            package=package,
        )

        chunks.append(chunk)
        current_name = name

    for child in node.children:
        chunks.extend(
            _collect_nodes_recursive(
                child,
                language,
                source,
                allowed_types,
                parent_name=current_name,
                depth=depth + 1,
                current_class=current_class,
                class_annotations=class_annotations,
                package=package,
            )
        )

    return chunks


# -----------------------------
# Public API
# -----------------------------

def extract_code_chunks(language: str, source: str) -> List[CodeChunk]:
    """
    Parse source and recursively extract structural definitions.

    Designed for vector DB indexing and context building.
    """
    tree: Tree = parse_code(language, source)
    root = tree.root_node

    allowed_types = TOP_LEVEL_NODE_TYPES.get(language, set())

    package = None
    if language == "java":
        package = _extract_package(root, source)

    return _collect_nodes_recursive(
        root,
        language,
        source,
        allowed_types,
        parent_name=None,
        depth=0,
        package=package,
    )
