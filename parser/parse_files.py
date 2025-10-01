import os
import json
from tree_sitter import Language, Parser

# Load compiled language library
LIB_PATH = 'build/my-languages.so'
LANGUAGES = {
    '.py': Language(LIB_PATH, 'python'),
    '.java': Language(LIB_PATH, 'java'),
    '.js': Language(LIB_PATH, 'javascript'),
    '.c': Language(LIB_PATH, 'c'),
    '.ts': Language(LIB_PATH, 'typescript'),
}

SOURCE_DIR = '../source_files/flask_app'
parser = Parser()

def get_node_text(node, code):
    return code[node.start_byte:node.end_byte].decode('utf-8')

def traverse(node, code, language, ir):
    # Functions
    if node.type in ['function_definition', 'function_declaration']:
        name_node = node.child_by_field_name('name')
        param_node = node.child_by_field_name('parameters')
        params = []
        if param_node:
            for p in param_node.children:
                if p.type == 'identifier':
                    params.append(get_node_text(p, code))
        ir['functions'].append({
            'name': get_node_text(name_node, code) if name_node else 'anonymous',
            'parameters': params,
            'start_line': node.start_point[0]+1,
            'end_line': node.end_point[0]+1
        })

    # Classes
    elif node.type in ['class_definition', 'class_declaration']:
        name_node = node.child_by_field_name('name')
        ir['classes'].append({
            'name': get_node_text(name_node, code) if name_node else 'anonymous',
            'start_line': node.start_point[0]+1,
            'end_line': node.end_point[0]+1
        })

    # Variables (simple approach for top-level assignments/declarations)
    elif node.type in ['variable_declarator', 'assignment', 'expression_statement']:
        text = get_node_text(node, code)
        ir['variables'].append({
            'name': text.split('=')[0].strip() if '=' in text else text.strip(),
            'line': node.start_point[0]+1
        })

    # Traverse children
    for child in node.children:
        traverse(child, code, language, ir)

# Main IR collection
all_ir = []

for filename in os.listdir(SOURCE_DIR):
    file_path = os.path.join(SOURCE_DIR, filename)
    ext = os.path.splitext(filename)[1]

    if ext in LANGUAGES:
        parser.set_language(LANGUAGES[ext])
        with open(file_path, 'rb') as f:
            code = f.read()

        tree = parser.parse(code)
        root_node = tree.root_node

        ir = {
            'file_name': filename,
            'language': ext[1:],  # py, java, js, c, ts
            'functions': [],
            'classes': [],
            'variables': []
        }

        traverse(root_node, code, ext[1:], ir)
        all_ir.append(ir)

# Save IR as JSON
with open('ir_output.json', 'w', encoding='utf-8') as f:
    json.dump(all_ir, f, indent=4)

print("IR generated for all files and saved to ir_output.json")
