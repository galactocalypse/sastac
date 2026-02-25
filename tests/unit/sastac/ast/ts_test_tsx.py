from tree_sitter import Parser, Language
from tree_sitter_typescript import language_tsx

parser = Parser()
parser.language = Language(language_tsx())

code = b"""
import React from "react";

type Props = {
  name: string;
};

export function Greeting({ name }: Props) {
  return (
    <div className="container">
      <h1>Hello {name}</h1>
    </div>
  );
}
"""

tree = parser.parse(code)

def print_tree(node, indent=0):
    print("  " * indent + f"{node.type} {node.start_point} -> {node.end_point}")
    for child in node.children:
        print_tree(child, indent + 1)


def find_jsx_elements(node, source):
    elements = []

    if node.type == "jsx_opening_element":
        name_node = node.child_by_field_name("name")
        if name_node:
            tag = source[name_node.start_byte:name_node.end_byte].decode()
            elements.append(tag)

    for child in node.children:
        elements.extend(find_jsx_elements(child, source))

    return elements

print_tree(tree.root_node)

jsx_tags = find_jsx_elements(tree.root_node, code)
print("JSX tags found:", jsx_tags)


