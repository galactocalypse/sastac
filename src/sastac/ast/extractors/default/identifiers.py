from dataclasses import dataclass, asdict
from typing import List, Optional

from tree_sitter import Node, Tree

from sastac.ast.parser import parse_code

def _extract_identifier(node: Node) -> Optional[str]:
    """
    Attempt to extract identifier/name across grammars.
    """
    for child in node.children:
        if child.type in {"identifier", "name"}:
            return child.text.decode("utf-8")
    return None
