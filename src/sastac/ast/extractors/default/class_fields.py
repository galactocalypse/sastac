from dataclasses import dataclass, asdict
from typing import List, Optional

from tree_sitter import Node, Tree

from sastac.ast.parser import parse_code
from sastac.ast.parser import TOP_LEVEL_NODE_TYPES


def _extract_class_fields(node: Node, source: bytes) -> list[dict[str, object]]:
    """
    Extract structured Java class fields.

    Includes:
    - name
    - type
    - modifiers
    - annotations
    - visibility
    - static/final flags
    - Javadoc above field (if present)
    - raw initializer (if present)

    Inline comments inside initializers are intentionally ignored.
    """

    fields: list[dict] = []

    for child in node.children:
        if child.type != "class_body":
            continue

        body_children = child.children

        for i, body_child in enumerate(body_children):
            if body_child.type != "field_declaration":
                continue

            # -------------------------
            # Extract Javadoc (if directly above)
            # -------------------------
            docstring = None
            if i > 0:
                prev_node = body_children[i - 1]
                if (
                    prev_node.type == "comment"
                    and prev_node.end_point[0] == body_child.start_point[0] - 1
                ):
                    text = source[
                        prev_node.start_byte:prev_node.end_byte
                    ].decode("utf-8").strip()

                    if text.startswith("/**"):
                        docstring = text

            field_type = None
            modifiers: list[str] = []
            annotations: list[str] = []
            visibility = None
            is_static = False
            is_final = False
            declarators: list[Node] = []

            # -------------------------
            # Parse field_declaration children
            # -------------------------
            for field_child in body_child.children:

                # Modifiers & annotations
                if field_child.type == "modifiers":
                    for mod in field_child.children:
                        mod_text = source[
                            mod.start_byte:mod.end_byte
                        ].decode("utf-8")

                        if mod.type == "annotation":
                            annotations.append(mod_text)
                        else:
                            modifiers.append(mod_text)

                            if mod_text in {"public", "private", "protected"}:
                                visibility = mod_text
                            if mod_text == "static":
                                is_static = True
                            if mod_text == "final":
                                is_final = True

                # Type handling
                if field_child.type in {
                    "type_identifier",
                    "generic_type",
                    "scoped_type_identifier",
                    "array_type",
                    "integral_type",
                    "floating_point_type",
                    "boolean_type",
                }:
                    field_type = source[
                        field_child.start_byte:field_child.end_byte
                    ].decode("utf-8")

                # Collect variable declarators
                if field_child.type == "variable_declarator":
                    declarators.append(field_child)

            # -------------------------
            # Emit one field per declarator
            # -------------------------
            for declarator in declarators:

                field_info = {
                    "name": None,
                    "type": field_type,
                    "modifiers": modifiers.copy(),
                    "annotations": annotations.copy(),
                    "visibility": visibility,
                    "is_static": is_static,
                    "is_final": is_final,
                    "docstring": docstring,
                    "initializer": None,
                }

                for var_child in declarator.children:

                    if var_child.type == "identifier":
                        field_info["name"] = source[
                            var_child.start_byte:var_child.end_byte
                        ].decode("utf-8")

                    # Any non-identifier child beyond '=' treated as initializer
                    if var_child.type not in {"identifier"}:
                        field_info["initializer"] = source[
                            var_child.start_byte:var_child.end_byte
                        ].decode("utf-8")

                if field_info["name"]:
                    fields.append(field_info)

    return fields
