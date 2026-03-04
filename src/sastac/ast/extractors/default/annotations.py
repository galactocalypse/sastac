from dataclasses import dataclass, asdict
from typing import List, Optional

from tree_sitter import Node, Tree

from sastac.ast.parser import parse_code
from sastac.ast.extractors.default.utils import _node_text


def _extract_annotations(node: Node, source: bytes) -> list[str]:
    anns = []
    modifiers_node = [child for child in node.children if child.type == "modifiers"]
    if modifiers_node:
        modifiers_node = modifiers_node[0]
        for child in modifiers_node.children:
            if child.type in {"annotation", "marker_annotation"}:
                anns.append(_node_text(child, source))
    return anns
