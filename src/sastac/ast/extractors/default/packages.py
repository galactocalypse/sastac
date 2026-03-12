from dataclasses import dataclass, asdict
from typing import List, Optional

from tree_sitter import Node, Tree

from sastac.ast.parser import parse_code
from .utils import _node_text

def _extract_package(root: Node, source: bytes) -> Optional[str]:
    for child in root.children:
        if child.type == "package_declaration":
            text = _node_text(child, source)
            return text.replace("package", "").replace(";", "").strip()
    return None


def _extract_imports(root_node: Node, source_bytes: bytes) -> list[str]:
    """
    Extract Java imports from the root AST node.

    Returns fully qualified import paths.
    """
    imports: list[str] = []

    for child in root_node.children:

        if child.type != "import_declaration":
            continue

        text = source_bytes[child.start_byte:child.end_byte].decode("utf-8")

        text = text.strip()

        if text.startswith("import"):
            text = text.replace("import", "", 1).strip()

        if text.endswith(";"):
            text = text[:-1]

        imports.append(text)

    return imports
