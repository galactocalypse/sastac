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
from sastac.ast.processor.constructor_processor import process_constructor_declaration
from sastac.ast.processor.file_processor import get_file_meta


SUPORTED_NODE_TYPES = {"method_declaration", "class_declaration", "function_definition", "method_definition", "constructor_declaration", "arrow_function", "interface_method_declaration"}




def extract_symbols(file_meta: FileMetadata) -> list[StructuralSymbol]:
    """
    Parse source and recursively extract structural definitions.

    Designed for vector DB indexing and context building.
    """
    tree: Tree = parse_code(file_meta.language, file_meta.body)
    if file_meta.language in ["java"]:
        file_meta.package = ext._extract_package(tree.root_node, file_meta.body)

    cursor = tree.walk()
    reached_root = False
    class_stack = list()
    total = 0
    processed = 0
    symbols: list[StructuralSymbol] = []
    while not reached_root:
        total += 1
        is_class_declaration = cursor.node.type == "class_declaration"
        if cursor.node and cursor.node.type in SUPORTED_NODE_TYPES:
            processed += 1
            symbol_info = process(file_meta, cursor.node, class_stack)
            if is_class_declaration:
                class_stack.append(symbol_info)
            if symbol_info:
                symbols.append(symbol_info)
        
        if cursor.goto_first_child():
            continue
        
        if cursor.goto_next_sibling():
            continue
        
        retracing = True
        while retracing:
            if not cursor.goto_parent():
                retracing = False
                reached_root = True
                if is_class_declaration:
                    class_stack.pop()
            if cursor.goto_next_sibling():
                retracing = False
    return symbols

def process(file_meta: FileMetadata, node: Node | None, class_stack: list[StructuralSymbol]) -> Optional[StructuralSymbol]:

    if not node:
        return

    if node.type == "class_declaration":
        symbol = process_class_type(file_meta, node)
        return symbol


    current_class_id = None
    current_class_name = None
    if class_stack:
        current_class = class_stack[-1]
        current_class_id = current_class.id
        current_class_name = current_class.name
    if node.type == "method_declaration":
        return process_method_declaration(
        file_meta,
        node,
        parent_class_id=current_class_id,
        parent_class_name=current_class_name,
    )
    if node.type == "constructor_declaration":
        return process_constructor_declaration(
        file_meta,
        node,
        parent_class_id=current_class_id,
        parent_class_name=current_class_name,
    )


if __name__ == "__main__":
    file_path = "/home/adarsh/code/booklore/booklore-api/src/main/java/org/booklore/config/security/SecurityConfig.java"
    file_meta = get_file_meta(file_path)
    symbols = extract_symbols(file_meta)
    for symbol in symbols:
        print(symbol)
