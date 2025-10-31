import ast
import json
import sys
import os

def parse_to_ast_json(file_path, output_json):
    """Parses a Python file into a structured AST JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    def node_to_dict(node):
        if isinstance(node, ast.AST):
            result = {"_type": node.__class__.__name__}
            for field, value in ast.iter_fields(node):
                result[field] = node_to_dict(value)
            return result
        elif isinstance(node, list):
            return [node_to_dict(x) for x in node]
        else:
            return value_to_str(value=node)

    def value_to_str(value):
        return value if isinstance(value, (int, float, str, bool)) or value is None else str(value)

    ast_dict = node_to_dict(tree)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_json)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(ast_dict, f, indent=2)

    print(f"✅ AST JSON saved to: {output_json}")
    return output_json

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ast_parser.py <input.py> <output.json>")
        sys.exit(1)

    parse_to_ast_json(sys.argv[1], sys.argv[2])
