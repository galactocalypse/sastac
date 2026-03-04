from dataclasses import dataclass, asdict
from tree_sitter import Parser, Language, Tree
from sastac.ast.parser import parse_code
from sastac.ast.parser import TOP_LEVEL_NODE_TYPES
from typing import List, Optional
import sastac.ast.extractors.default as ext
from tree_sitter import Node, Tree
import hashlib
from pathlib import Path
import json
from sastac.ast.models.symbol import StructuralSymbol
from sastac.ast.models.file_meta import FileMetadata
from sastac.ast.processor.class_processor import process_class_type
from sastac.ast.processor.file_processor import get_file_meta


def process_method_declaration(
    file_meta: FileMetadata,
    node: Node,
    parent_class_id: str | None,
    parent_class_name: str | None,
) -> Optional[StructuralSymbol]:
    """
    Extract structured information from a Java method_declaration node.
    """

    source = file_meta.body

    # -------------------------
    # Extract name
    # -------------------------
    name_node = node.child_by_field_name("name")
    if not name_node:
        return None

    method_name = source[
        name_node.start_byte:name_node.end_byte
    ].decode("utf-8")

    # -------------------------
    # Stable ID
    # -------------------------
    symbol_id = hashlib.sha256(
        (file_meta.hash + method_name + str(node.start_byte)).encode("utf-8")
    ).hexdigest()

    # -------------------------
    # Extract signature
    # -------------------------
    signature = ext._extract_signature(node, source)

    # -------------------------
    # Extract annotations
    # -------------------------
    annotations = ext._extract_annotations(node, source)

    # -------------------------
    # Extract modifiers + return type
    # -------------------------
    modifiers = []
    visibility = None
    return_type = None
    is_static = False
    is_abstract = False

    for child in node.children:

        if child.type == "modifiers":
            for mod in child.children:
                if mod.type == "marker_annotation":
                    continue
                text = source[
                    mod.start_byte:mod.end_byte
                ].decode("utf-8")
                modifiers.append(text)

                if text in {"public", "private", "protected"}:
                    visibility = text
                if text == "static":
                    is_static = True
                if text == "abstract":
                    is_abstract = True

        # Return type
        if child.type in {
            "type_identifier",
            "generic_type",
            "scoped_type_identifier",
            "array_type",
            "integral_type",
            "floating_point_type",
            "boolean_type",
            "void_type",
        }:
            return_type = source[
                child.start_byte:child.end_byte
            ].decode("utf-8")

    # -------------------------
    # Extract parameters
    # -------------------------
    parameters = []

    params_node = node.child_by_field_name("parameters")
    if params_node:
        for param in params_node.named_children:
            if param.type == "formal_parameter":
                param_type = None
                param_name = None

                for p_child in param.children:
                    if p_child.type in {
                        "type_identifier",
                        "generic_type",
                        "scoped_type_identifier",
                        "array_type",
                        "integral_type",
                        "floating_point_type",
                        "boolean_type",
                    }:
                        param_type = source[
                            p_child.start_byte:p_child.end_byte
                        ].decode("utf-8")

                    if p_child.type == "identifier":
                        param_name = source[
                            p_child.start_byte:p_child.end_byte
                        ].decode("utf-8")

                parameters.append({
                    "name": param_name,
                    "type": param_type,
                })

    # -------------------------
    # Extract docstring
    # -------------------------
    docstring = ext._extract_docstring(node, file_meta.language, source)

    # -------------------------
    # Extract body
    # -------------------------
    body = source[node.start_byte:node.end_byte]

    # -------------------------
    # Build metadata
    # -------------------------
    metadata = {
        "package": file_meta.package,
        "annotations": annotations,
        "signature": signature,
        "class": parent_class_name,
        "return_type": return_type,
        "parameters": parameters,
        "visibility": visibility,
        "modifiers": modifiers,
        "is_static": is_static,
        "is_abstract": is_abstract,
        "docstring": docstring,
    }

    return StructuralSymbol(
        id=symbol_id,
        type="method",
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
        name=method_name,
        parent_id=parent_class_id,
        body=body,
        metadata=metadata,
    )

