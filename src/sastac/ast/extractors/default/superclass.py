from dataclasses import dataclass, asdict
from typing import List, Optional

from tree_sitter import Node, Tree

from sastac.ast.parser import parse_code


def _extract_superclass(class_node, source_code) -> str | None:
    # Retrieve the 'superclass' field node
    superclass_node = class_node.child_by_field_name('superclass')
    
    if superclass_node:
        # The node typically contains the 'extends' keyword and the type
        # You can extract the whole node or just the type identifier
        return source_code[superclass_node.start_byte : superclass_node.end_byte].decode('utf8')
    return None


