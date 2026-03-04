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

