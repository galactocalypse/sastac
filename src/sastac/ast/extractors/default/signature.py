from dataclasses import dataclass, asdict
from typing import List, Optional

from tree_sitter import Node, Tree

from sastac.ast.parser import parse_code

def _extract_signature(node: Node, source: bytes) -> str | None:
    """
    Extract structural declaration signature (excluding annotations).

    Supports:
    - class_declaration
    - method_declaration
    - constructor_declaration

    Works whether annotations are:
    - separate nodes
    - nested inside 'modifiers'
    """

    if node.type not in {
        "class_declaration",
        "method_declaration",
        "constructor_declaration",
    }:
        return None

    signature_start = None

    # ----------------------------------------
    # Find first non-annotation token
    # ----------------------------------------
    for child in node.children:

        # Case 1: annotations as separate nodes
        if child.type in {"marker_annotation", "annotation"}:
            continue

        # Case 2: annotations inside modifiers
        if child.type == "modifiers":
            for mod in child.children:
                if mod.type in {"marker_annotation", "annotation"}:
                    continue
                # first real modifier (public/static/etc.)
                signature_start = mod.start_byte
                break

            if signature_start is not None:
                break

            continue

        # First structural token (class keyword, return type, etc.)
        signature_start = child.start_byte
        break

    if signature_start is None:
        return None

    # ----------------------------------------
    # End before body block
    # ----------------------------------------
    body_node = node.child_by_field_name("body")

    if body_node:
        signature_end = body_node.start_byte
    else:
        signature_end = node.end_byte

    signature = source[signature_start:signature_end].decode("utf-8")

    return signature.strip()
