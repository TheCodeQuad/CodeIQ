import os
import json
from pathlib import Path

# --- Load Tree-sitter for Python (0.25+ compatible) ---
try:
    # Try using the tree-sitter-python package (recommended)
    import tree_sitter_python
    from tree_sitter import Language, Parser
    
    # Get the language as a PyCapsule and wrap it in Language
    PY_LANGUAGE = Language(tree_sitter_python.language())
    parser = Parser(PY_LANGUAGE)
    
except ImportError as e:
    # Fallback: try loading compiled library manually
    try:
        from tree_sitter import Language, Parser
        
        # Look for compiled library
        PARSER_DIR = Path(__file__).parent
        
        # Try different possible library names
        possible_libs = [
            PARSER_DIR / "build" / "python_lang.dll",
            PARSER_DIR / "build" / "python_lang.so",
            PARSER_DIR / "build" / "python_lang.dylib",
            PARSER_DIR / "tree-sitter-python.dll",
            PARSER_DIR / "tree-sitter-python.so",
        ]
        
        lib_path = None
        for lib in possible_libs:
            if lib.exists():
                lib_path = lib
                break
        
        if lib_path is None:
            raise FileNotFoundError(
                "No compiled tree-sitter Python library found. "
                "Please install tree-sitter-python package:\n"
                "  pip install tree-sitter-python\n"
                "Or compile manually using tree-sitter CLI."
            )
        
        PY_LANGUAGE = Language(str(lib_path), "python")
        parser = Parser(PY_LANGUAGE)
        
    except Exception as e:
        import sys
        print("Failed to load tree-sitter Python language:", str(e), file=sys.stderr)
        print("\nTo fix this, install the tree-sitter-python package:", file=sys.stderr)
        print("  pip install tree-sitter-python", file=sys.stderr)
        raise

# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------
def get_node_text(source_code, node):
    """Return text for a given node."""
    return source_code[node.start_byte:node.end_byte].decode("utf-8").strip()

def extract_docstring(source_code, node):
    """Extracts docstring if the first child is a string."""
    if node.child_count > 0:
        first_child = node.children[0]
        if first_child.type == "expression_statement" and first_child.child_count > 0:
            string_node = first_child.children[0]
            if string_node.type == "string":
                return get_node_text(source_code, string_node).strip("\"'").strip()
    return None

def extract_parameters(node, source_code):
    """Extract parameters from function_definition or parameters node."""
    params = []
    for child in node.children:
        if child.type == "identifier":
            params.append({"name": get_node_text(source_code, child), "type": None})
        elif child.type == "typed_parameter":
            name_node = child.child_by_field_name("name")
            type_node = child.child_by_field_name("type")
            params.append({
                "name": get_node_text(source_code, name_node) if name_node else None,
                "type": get_node_text(source_code, type_node) if type_node else None
            })
    return params

def extract_calls(node, source_code):
    """Recursively find all function calls."""
    calls = []
    def traverse(n):
        if n.type == "call":
            func_node = n.child_by_field_name("function")
            if func_node:
                calls.append(get_node_text(source_code, func_node))
        for c in n.children:
            traverse(c)
    traverse(node)
    return list(set(calls))

def extract_assignments(node, source_code):
    """Get top-level variable assignments."""
    vars_ = []
    if node.type == "assignment":
        left = node.child_by_field_name("left")
        if left and left.type == "identifier":
            vars_.append(get_node_text(source_code, left))
    for c in node.children:
        vars_.extend(extract_assignments(c, source_code))
    return vars_

# ---------------------------------------------------------
# Core parsing functions
# ---------------------------------------------------------
def parse_python_file(file_path):
    """
    Parses a Python file and extracts structured IR data:
    functions, classes, imports, variables, etc.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    source_bytes = source.encode("utf-8")
    tree = parser.parse(source_bytes)
    root = tree.root_node

    file_ir = {
        "path": file_path,
        "imports": [],
        "classes": [],
        "functions": [],
        "variables": []
    }

    def traverse(node):
        # ---- Imports ----
        if node.type in ("import_statement", "import_from_statement"):
            file_ir["imports"].append(get_node_text(source_bytes, node))

        # ---- Class Definitions ----
        elif node.type == "class_definition":
            class_name_node = node.child_by_field_name("name")
            base_node = node.child_by_field_name("superclasses")
            docstring = extract_docstring(source_bytes, node)
            class_info = {
                "name": get_node_text(source_bytes, class_name_node) if class_name_node else None,
                "base_classes": get_node_text(source_bytes, base_node) if base_node else None,
                "docstring": docstring,
                "methods": []
            }

            # find methods inside class
            for c in node.children:
                if c.type == "function_definition":
                    func_info = extract_function(c, source_bytes)
                    class_info["methods"].append(func_info)

            file_ir["classes"].append(class_info)

        # ---- Function Definitions ----
        elif node.type == "function_definition":
            func_info = extract_function(node, source_bytes)
            file_ir["functions"].append(func_info)

        # ---- Variables ----
        elif node.type == "assignment":
            file_ir["variables"].extend(extract_assignments(node, source_bytes))

        # Recurse
        for c in node.children:
            traverse(c)

    def extract_function(node, source_code):
        """Extract info for one function node."""
        name_node = node.child_by_field_name("name")
        params_node = node.child_by_field_name("parameters")
        return_node = node.child_by_field_name("return_type")
        body_node = node.child_by_field_name("body")

        return {
            "name": get_node_text(source_code, name_node) if name_node else None,
            "parameters": extract_parameters(params_node, source_code) if params_node else [],
            "return_type": get_node_text(source_code, return_node) if return_node else None,
            "docstring": extract_docstring(source_code, node),
            "calls": extract_calls(body_node, source_code) if body_node else [],
            "variables": extract_assignments(body_node, source_code) if body_node else [],
            "start_line": node.start_point[0] + 1,
            "end_line": node.end_point[0] + 1
        }

    traverse(root)
    return file_ir

def parse_python_repo(repo_path):
    """
    Walk through a Python repository and parse all `.py` files using Tree-sitter.
    Skips heavy folders like venv, build, node_modules, etc.
    """
    skip_dirs = {"venv", "__pycache__", "build", "dist", ".git", "node_modules", ".mypy_cache"}
    ir_data = {"repo_path": repo_path, "files": []}

    for root, dirs, files in os.walk(repo_path):
        # modify dirs in-place to skip unwanted ones
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    parsed = parse_python_file(file_path)
                    ir_data["files"].append(parsed)
                except Exception as e:
                    ir_data["files"].append({"path": file_path, "error": str(e)})

    return ir_data


# ---------------------------------------------------------
# CLI test
# ---------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        target = sys.argv[1]
        if os.path.isdir(target):
            result = parse_python_repo(target)
        else:
            result = parse_python_file(target)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("✅ Python parser initialized successfully!")
