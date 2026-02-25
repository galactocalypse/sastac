from tree_sitter import Parser, Language
import tree_sitter_java

def test_parse_java():
    """Test that we can parse a Java file."""
    parser = Parser()
    parser.language = Language(tree_sitter_java.language())
    tree = parser.parse(b"class Main { void main() {}}")
    print(tree.root_node)
