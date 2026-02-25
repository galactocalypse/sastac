import pytest
from tree_sitter import Tree

from sastac.ast.parser import (
    parse_code,
    get_parser,
    LANGUAGE_REGISTRY,
)


# Minimal valid snippets per language
VALID_SNIPPETS = {
    "python": "def foo():\n    return 1",
    "javascript": "function foo() { return 1; }",
    "typescript": "function foo(): number { return 1; }",
    "tsx": "const x = <div>Hello</div>;",
    "go": "package main\nfunc main() {}",
    "java": "class A { int x; }",
}


# -----------------------------
# Registered languages parse successfully
# -----------------------------

@pytest.mark.parametrize("language", list(LANGUAGE_REGISTRY.keys()))
def test_registered_languages_parse(language):
    source = VALID_SNIPPETS[language]

    tree = parse_code(language, source)

    assert isinstance(tree, Tree)
    assert tree.root_node is not None
    assert not tree.root_node.has_error


# -----------------------------
# Unsupported language raises error
# -----------------------------

def test_unsupported_language_raises():
    with pytest.raises(ValueError):
        get_parser("rust")


def test_parse_code_unsupported_language():
    with pytest.raises(ValueError):
        parse_code("rust", "fn main() {}")


# -----------------------------
# Parser caching works
# -----------------------------

def test_get_parser_is_cached():
    parser1 = get_parser("python")
    parser2 = get_parser("python")

    # Same object reference means caching is working
    assert parser1 is parser2
