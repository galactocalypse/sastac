from dataclasses import dataclass, asdict
from typing import List, Optional

from tree_sitter import Node, Tree

from sastac.ast.parser import parse_code
from sastac.ast.parser import TOP_LEVEL_NODE_TYPES
import sastac.ast.extractors.default as ext

def _extract_constructors(class_node, source_code) -> list[dict]:
    constructors = []
    
    # 1. Get the class body node
    body_node = class_node.child_by_field_name('body')
    if not body_node:
        return constructors

    # 2. Iterate through children of the body
    for child in body_node.children:
        if child.type == 'constructor_declaration':
            # Extract the full text of the constructor
            constructor_text = source_code[child.start_byte:child.end_byte].decode('utf8')
            
            # Extract specific fields if needed
            name_node = child.child_by_field_name('name')
            params_node = child.child_by_field_name('parameters')
            
            name = source_code[name_node.start_byte:name_node.end_byte].decode('utf8')
            params = source_code[params_node.start_byte:params_node.end_byte].decode('utf8')
            
            constructors.append({
                "full_text": constructor_text,
                "name": name,
                "parameters": params
            })
            
    return constructors

