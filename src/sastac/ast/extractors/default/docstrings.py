from tree_sitter import Node, Tree
from .utils import _node_text
from typing import List, Optional

def _extract_docstring(node: Node, language: str, source: bytes) -> str | None:
    """
    Extract the Javadoc block immediately preceding the given node.

    Rules:
    - Must be in the same parent (e.g., class_body)
    - Only attaches the closest Javadoc (/** ... */)
    - Skips annotations and non-Javadoc comments
    - Stops at any structural declaration
    """

    parent = node.parent
    if not parent:
        return None

    siblings = parent.children
    try:
        idx = siblings.index(node)
    except ValueError:
        return None

    j = idx - 1

    while j >= 0:
        prev = siblings[j]

        # Skip annotations
        if prev.type in {"annotation", "marker_annotation"}:
            j -= 1
            continue

        # Handle comments
        if prev.type in {"block_comment", "comment"}:
            text = source[
                prev.start_byte:prev.end_byte
            ].decode("utf-8").strip()

            # Only attach Javadoc
            if text.startswith("/**"):
                return text

            # Non-Javadoc comment — skip but keep looking
            j -= 1
            continue

        # Skip line comments (// ...)
        if prev.type == "line_comment":
            j -= 1
            continue

        # Any other structural node — stop searching
        break

    return None
