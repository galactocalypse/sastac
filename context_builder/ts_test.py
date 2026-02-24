from tree_sitter import Parser, Language
import tree_sitter_typescript as python_lang

parser = Parser()

# Wrap the PyCapsule into a Language object
PY_LANGUAGE = Language(python_lang.language())

parser.language = PY_LANGUAGE

tree = parser.parse(b"class Main { void main() {}}")
print(tree.root_node)