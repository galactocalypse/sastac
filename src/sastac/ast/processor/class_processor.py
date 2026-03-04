from tree_sitter import Node, Tree
from sastac.ast.models.symbol import StructuralSymbol
from sastac.ast.models.file_meta import FileMetadata
import sastac.ast.extractors.default as ext
import hashlib

def process_class_type(file_meta: FileMetadata, node: Node) -> StructuralSymbol:
    class_source = file_meta.body
    symbol_name_node = node.child_by_field_name("name")
    if not symbol_name_node:
        raise Exception("Could not extract class name")
    symbol_name = ext._node_text(symbol_name_node, class_source)
    symbol_id = hashlib.sha256((file_meta.hash + symbol_name + str(node.start_byte)).encode("utf-8")).hexdigest()

    return StructuralSymbol(
        id=symbol_id,
        type=node.type,
        name=symbol_name,
        parent_id=None,
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
        body=file_meta.body[node.start_byte:node.end_byte],
        metadata={
            "package": file_meta.package,     
            "annotations": ext._extract_annotations(node, class_source),
            "signature": ext._extract_signature(node, class_source),
            "superclass": ext._extract_superclass(node, class_source),
            "interfaces": ext._extract_interfaces(node, class_source),
            "constructors": ext._extract_constructors(node, class_source),
            "fields": ext._extract_class_fields(node, class_source)
        }
    )
