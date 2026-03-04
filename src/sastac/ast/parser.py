from functools import lru_cache
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript
import tree_sitter_go
import tree_sitter_java
from tree_sitter import Parser, Language, Tree


LANGUAGE_REGISTRY = {
    "python": tree_sitter_python,
    "javascript": tree_sitter_javascript,
    "typescript": tree_sitter_typescript,
    "tsx": tree_sitter_typescript,
    "go": tree_sitter_go,
    "java": tree_sitter_java,
}

TOP_LEVEL_NODE_TYPES = {
    "python": {"function_definition", "class_definition"},
    "javascript": {"function_declaration", "class_declaration", "method_definition"},
    "typescript": {"function_declaration", "class_declaration", "method_definition"},
    "go": {"function_declaration", "method_declaration"},
    "java": {"class_declaration",
        "method_declaration",
        "interface_declaration",
        "enum_declaration",
        "constructor_declaration",
        "annotation_type_declaration",
        "record_declaration",
    },
}

@lru_cache
def get_parser(language: str) -> Parser:
    if language not in LANGUAGE_REGISTRY:
        raise ValueError(f"Unsupported language: {language}")

    parser = Parser()

    if language == "typescript":
        capsule = tree_sitter_typescript.language_typescript()
    elif language == "tsx":
        capsule = tree_sitter_typescript.language_tsx()
    else:
        capsule = LANGUAGE_REGISTRY[language].language()

    parser.language = Language(capsule)
    return parser


def parse_code(language: str, source: bytes) -> Tree:
    parser = get_parser(language)
    return parser.parse(source)
