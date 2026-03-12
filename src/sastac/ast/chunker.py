from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from tree_sitter import Node

from sastac.ast.parser import parse_code, TOP_LEVEL_NODE_TYPES


# -------------------------------------------------------
# CodeChunk dataclass
# -------------------------------------------------------

@dataclass
class CodeChunk:
    name: Optional[str]
    node_type: str
    language: str
    depth: int
    parent_name: Optional[str]
    signature: str
    docstring: Optional[str]
    body: str
    start_byte: int
    end_byte: int
    start_line: int
    end_line: int

    def to_metadata(self) -> dict:
        return {
            "name": self.name,
            "node_type": self.node_type,
            "language": self.language,
            "depth": self.depth,
            "parent_name": self.parent_name,
            "signature": self.signature,
            "docstring": self.docstring,
            "start_line": self.start_line,
            "end_line": self.end_line,
        }


# -------------------------------------------------------
# Language-specific node types to extract
# -------------------------------------------------------

EXTRACTABLE_NODE_TYPES = {
    "python": {"function_definition", "class_definition"},
    "javascript": {"function_declaration", "class_declaration", "method_definition", "arrow_function"},
    "typescript": {"function_declaration", "class_declaration", "method_definition", "arrow_function"},
    "tsx": {"function_declaration", "class_declaration", "method_definition", "arrow_function"},
    "go": {"function_declaration", "method_declaration"},
    "java": {
        "class_declaration",
        "method_declaration",
        "interface_declaration",
        "enum_declaration",
        "constructor_declaration",
        "annotation_type_declaration",
        "record_declaration",
    },
}

# Node type -> "name" child field name (language-specific)
NAME_FIELD = "name"


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------

def _get_node_name(node: Node, source_bytes: bytes) -> Optional[str]:
    """Extract the declared name from a node."""
    name_node = node.child_by_field_name(NAME_FIELD)
    if name_node:
        return source_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8", errors="replace")
    return None


def _extract_docstring(node: Node, source_bytes: bytes, language: str) -> Optional[str]:
    """Extract docstring/leading comment if present."""
    if language == "python":
        # For Python, docstring is the first expression_statement child containing a string
        for child in node.children:
            if child.type == "block":
                for stmt in child.children:
                    if stmt.type == "expression_statement":
                        for inner in stmt.children:
                            if inner.type == "string":
                                raw = source_bytes[inner.start_byte:inner.end_byte].decode("utf-8", errors="replace")
                                return raw.strip("\"'").strip()
                        break
                    elif stmt.type not in ("comment", "\n"):
                        break
    return None


def _extract_signature(node: Node, source_bytes: bytes) -> str:
    """Extract a one-line signature (first line of the node, or up to opening brace)."""
    text = source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
    first_line = text.split("\n")[0].strip()
    return first_line


# -------------------------------------------------------
# Recursive walker
# -------------------------------------------------------

def _walk(
    node: Node,
    source_bytes: bytes,
    language: str,
    extractable: set,
    depth: int,
    parent_name: Optional[str],
    results: List[CodeChunk],
):
    if node.type in extractable:
        name = _get_node_name(node, source_bytes)
        docstring = _extract_docstring(node, source_bytes, language)
        signature = _extract_signature(node, source_bytes)
        body = source_bytes[node.start_byte:node.end_byte]

        chunk = CodeChunk(
            name=name,
            node_type=node.type,
            language=language,
            depth=depth,
            parent_name=parent_name,
            signature=signature,
            docstring=docstring,
            body=source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace"),
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            start_line=node.start_point[0],
            end_line=node.end_point[0],
        )
        results.append(chunk)

        # Recurse into children with increased depth and this node as parent
        for child in node.children:
            _walk(child, source_bytes, language, extractable, depth + 1, name, results)
    else:
        for child in node.children:
            _walk(child, source_bytes, language, extractable, depth, parent_name, results)


# -------------------------------------------------------
# Public API
# -------------------------------------------------------

def extract_code_chunks(language: str, source: str | bytes) -> List[CodeChunk]:
    """
    Parse `source` for the given language and return a list of CodeChunk objects
    for every extractable node (class, function, method, etc.).
    """
    if isinstance(source, str):
        source_bytes = source.encode("utf-8")
    else:
        source_bytes = source

    tree = parse_code(language, source_bytes)
    extractable = EXTRACTABLE_NODE_TYPES.get(language, set())

    results: List[CodeChunk] = []
    _walk(tree.root_node, source_bytes, language, extractable, depth=1, parent_name=None, results=results)
    return results
