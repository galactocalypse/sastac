from tree_sitter import Parser, Language
from tree_sitter_typescript import language_typescript

parser = Parser()
parser.language = Language(language_typescript())

code = b"""
function add(a: number, b: number) {
  return a + b;
}
"""

tree = parser.parse(code)
print(tree.root_node)
