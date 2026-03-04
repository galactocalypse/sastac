
def _extract_interfaces(class_node, source_code) -> str | None:
    # Retrieve the 'interfaces' field node
    interfaces_node = class_node.child_by_field_name('interfaces')
    
    if interfaces_node:
        # This node includes the 'implements' keyword and a type_list
        return source_code[interfaces_node.start_byte : interfaces_node.end_byte].decode('utf8')
    return None
