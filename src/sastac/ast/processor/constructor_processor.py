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
from sastac.ast.processor.method_processor import process_method_declaration
from sastac.ast.processor.file_processor import get_file_meta
import sastac.ast.extractors.default


def process_constructor_declaration(
    file_meta: FileMetadata,
    node: Node,
    parent_class_id: str | None,
    parent_class_name: str | None,
) -> Optional[StructuralSymbol]:

    source = file_meta.body

    name_node = node.child_by_field_name("name")
    if not name_node:
        return None

    constructor_name = source[
        name_node.start_byte:name_node.end_byte
    ].decode("utf-8")

    symbol_id = hashlib.sha256(
        (file_meta.hash + constructor_name + str(node.start_byte)).encode("utf-8")
    ).hexdigest()

    annotations = ext._extract_annotations(node, source)

    # -------------------------
    # Modifiers (exclude annotations)
    # -------------------------
    modifiers = []
    visibility = None

    for child in node.children:
        if child.type == "modifiers":
            for mod in child.children:
                text = source[
                    mod.start_byte:mod.end_byte
                ].decode("utf-8").strip()

                if mod.type in {"marker_annotation", "annotation"}:
                    continue

                modifiers.append(text)

                if text in {"public", "private", "protected"}:
                    visibility = text

    # -------------------------
    # Parameters
    # -------------------------
    parameters = []
    params_node = node.child_by_field_name("parameters")

    if params_node:
        for param in params_node.named_children:
            if param.type == "formal_parameter":
                param_name = None
                param_type = None

                for p in param.children:
                    if p.type == "identifier":
                        param_name = source[p.start_byte:p.end_byte].decode("utf-8")
                    elif p.type != "modifiers":
                        param_type = source[p.start_byte:p.end_byte].decode("utf-8")

                parameters.append({
                    "name": param_name,
                    "type": param_type
                })

    # -------------------------
    # Improved Docstring Extraction
    # -------------------------

    docstring = ext._extract_docstring(node, file_meta.language, source)

    signature = ext._extract_signature(node, source)
    body = source[node.start_byte:node.end_byte]

    metadata = {
        "package": file_meta.package,
        "annotations": annotations,
        "signature": signature,
        "class": parent_class_name,
        "parameters": parameters,
        "visibility": visibility,
        "modifiers": modifiers,
        "is_static": False,
        "is_abstract": False,
        "docstring": docstring,
    }

    return StructuralSymbol(
        id=symbol_id,
        type="constructor",
        name=constructor_name,
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
        parent_id=parent_class_id,
        body=body,
        metadata=metadata,
    )
