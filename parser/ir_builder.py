import os
from tree_sitter import Language, Parser

# Load compiled languages (run tree-sitter build once before using)
LIB_PATH = os.path.join(os.path.dirname(__file__), "build", "my-languages.so")

LANGUAGES = {
    "python": Language(LIB_PATH, "python"),
    "java": Language(LIB_PATH, "java"),
    "c": Language(LIB_PATH, "c"),
    "javascript": Language(LIB_PATH, "javascript")
}

def parse_file(file_path: str, language: str):
    """
    Parses a source file and returns an IR node (AST tree).
    """
    parser = Parser()
    parser.set_language(LANGUAGES[language])

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        raise RuntimeError(f"Error reading file {file_path}: {e}")

    tree = parser.parse(bytes(code, "utf8"))
    root_node = tree.root_node

    return IRNode(
        type=root_node.type,
        start=root_node.start_point,
        end=root_node.end_point,
        children=_parse_children(root_node)
    )

def _parse_children(node):
    """Recursively converts a Tree-sitter node to IRNode structure."""
    children = []
    for child in node.children:
        children.append(
            IRNode(
                type=child.type,
                start=child.start_point,
                end=child.end_point,
                children=_parse_children(child)
            )
        )
    return children

class IRNode:
    """Simple intermediate representation of syntax tree nodes."""
    def __init__(self, type, start, end, children=None):
        self.type = type
        self.start = start
        self.end = end
        self.children = children or []

    def to_dict(self):
        return {
            "type": self.type,
            "start": self.start,
            "end": self.end,
            "children": [child.to_dict() for child in self.children]
        }
