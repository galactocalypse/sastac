import pytest
from tree_sitter import Tree

from sastac.ast.parser import (
    parse_code,
    get_parser,
    LANGUAGE_REGISTRY,
)
from sastac.ast.chunker import extract_code_chunks


# ---------------------------------------------------------
# Minimal valid snippets per language
# ---------------------------------------------------------

VALID_SNIPPETS = {
    "python": "def foo():\n    return 1",
    "javascript": "function foo() { return 1; }",
    "typescript": "function foo(): number { return 1; }",
    "tsx": "const x = <div>Hello</div>;",
    "go": "package main\nfunc main() {}",
    "java": "class A { int x; }",
}


# ---------------------------------------------------------
# Registered languages parse successfully
# ---------------------------------------------------------

@pytest.mark.parametrize("language", list(LANGUAGE_REGISTRY.keys()))
def test_registered_languages_parse(language):
    source = VALID_SNIPPETS[language]

    tree = parse_code(language, source)

    assert isinstance(tree, Tree)
    assert tree.root_node is not None
    assert not tree.root_node.has_error


# ---------------------------------------------------------
# Unsupported language raises error
# ---------------------------------------------------------

def test_unsupported_language_raises():
    with pytest.raises(ValueError):
        get_parser("rust")


def test_parse_code_unsupported_language():
    with pytest.raises(ValueError):
        parse_code("rust", "fn main() {}")


# ---------------------------------------------------------
# Parser caching works
# ---------------------------------------------------------

def test_get_parser_is_cached():
    parser1 = get_parser("python")
    parser2 = get_parser("python")
    assert parser1 is parser2


# =========================================================
# NEW: Java-specific tests
# =========================================================

JAVA_SAMPLE = """
package com.example;

import org.springframework.web.bind.annotation.*;

@RestController
public class BookController {

    private final BookService service;

    public BookController(BookService service) {
        this.service = service;
    }

    @GetMapping("/books")
    public List<Book> getBooks() {
        return service.getAll();
    }
}
"""


def test_java_ast_contains_expected_nodes():
    """
    Ensure Java AST actually contains class/method nodes.
    """
    tree = parse_code("java", JAVA_SAMPLE)
    root = tree.root_node

    node_types = set()

    def walk(node):
        node_types.add(node.type)
        for c in node.children:
            walk(c)

    walk(root)

    assert "class_declaration" in node_types
    assert "method_declaration" in node_types


def test_java_chunk_extraction_returns_chunks():
    """
    Ensure chunker extracts useful chunks from Java code.
    """
    chunks = extract_code_chunks("java", JAVA_SAMPLE)

    assert len(chunks) > 0

    names = [c.name for c in chunks if c.name]
    assert "BookController" in names or "getBooks" in names


def test_java_constructor_extraction():
    """
    Constructor should also be extracted.
    """
    src = """
    class A {
        public A() {}
    }
    """
    chunks = extract_code_chunks("java", src)

    assert any("A" in (c.name or "") for c in chunks)


def test_java_interface_extraction():
    """
    Interfaces common in Spring apps.
    """
    src = """
    interface BookRepository {
        void save(Book b);
    }
    """
    chunks = extract_code_chunks("java", src)

    assert len(chunks) > 0


def test_realistic_spring_controller():
    """
    Simulates Booklore backend controller.
    """
    src = """
    @RestController
    public class AuthController {

        @PostMapping("/login")
        public Token login(User u) {
            return new Token();
        }
    }
    """

    chunks = extract_code_chunks("java", src)

    assert len(chunks) >= 1
    assert any("AuthController" in (c.name or "") for c in chunks)
