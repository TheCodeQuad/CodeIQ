from tree_sitter import Parser
from tree_sitter_languages import get_language
import json

# Initialize Tree-sitter for Python
PYTHON = get_language('python')
parser = Parser()
parser.set_language(PYTHON)


def parse_code_to_ast(code: str):
    """Return Tree-sitter raw AST tree for Python code"""
    tree = parser.parse(bytes(code, "utf8"))
    return tree


def build_ir_from_ast(tree, code: str):
    """
    Build simplified IR from the Tree-sitter AST of Python code.
    Example IR:
      {
        "imports": [...],
        "classes": [...],
        "functions": [...]
      }
    """
    root = tree.root_node
    lines = code.splitlines()
    ir = {"imports": [], "classes": [], "functions": []}

    def walk(node):
        t = node.type
        if t == "import_statement" or t == "import_from_statement":
            ir["imports"].append(lines[node.start_point[0]].strip())

        elif t == "class_definition":
            name_node = node.child_by_field_name("name")
            ir["classes"].append({
                "name": name_node.text.decode("utf8") if name_node else "AnonymousClass",
                "start": node.start_point[0] + 1,
                "end": node.end_point[0] + 1
            })

        elif t == "function_definition":
            name_node = node.child_by_field_name("name")
            ir["functions"].append({
                "name": name_node.text.decode("utf8") if name_node else "anonymous",
                "start": node.start_point[0] + 1,
                "end": node.end_point[0] + 1
            })

        for child in node.children:
            walk(child)

    walk(root)
    return ir


if __name__ == "__main__":
    # quick standalone test
    sample_code = """
import os
import sys

class Navigator:
    def __init__(self):
        pass

def main():
    print("Hello world")
"""
    tree = parse_code_to_ast(sample_code)
    ir = build_ir_from_ast(tree, sample_code)
    print(json.dumps(ir, indent=2))
