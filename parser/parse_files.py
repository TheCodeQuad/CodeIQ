import os
import json
from tree_sitter import Language, Parser

# -------------------------------
# CONFIGURATION
# -------------------------------
LIB_PATH = 'build/my-languages.so'  # your compiled languages
LANGUAGES = {
    '.py': Language(LIB_PATH, 'python'),
    '.java': Language(LIB_PATH, 'java'),
    '.js': Language(LIB_PATH, 'javascript'),
    '.c': Language(LIB_PATH, 'c'),
}

SOURCE_DIR = '../source_files'
parser = Parser()


# -------------------------------
# HELPER FUNCTIONS
# -------------------------------
def get_node_text(node, code):
    return code[node.start_byte:node.end_byte].decode('utf-8')


def extract_docstring(node, code):
    """Extract Python docstring if present"""
    if node.type == 'function_definition':
        body = node.child_by_field_name('body')
        if body and len(body.children) > 0:
            first_stmt = body.children[0]
            if first_stmt.type == 'expression_statement':
                expr = first_stmt.children[0]
                if expr.type in ['string', 'string_literal']:
                    return get_node_text(expr, code).strip('"\'')
    return None


def extract_return_type(node, code, language):
    """Extract return type for Java/C"""
    if language in ['java', 'c']:
        type_node = node.child_by_field_name('type')
        if type_node:
            return get_node_text(type_node, code)
        # For C: sometimes type is a direct child
        for child in node.children:
            if child.type in ['primitive_type', 'type_identifier']:
                return get_node_text(child, code)
    return None


def extract_decorators(node, code):
    """Python decorators"""
    decorators = []
    for child in node.children:
        if child.type == 'decorator':
            decorators.append(get_node_text(child, code))
    return decorators


def extract_parameters(param_node, code):
    """Extract parameters info"""
    params = []
    if not param_node:
        return params

    for child in param_node.children:
        if child.type in ['identifier', 'parameter', 'formal_parameter', 'typed_parameter', 'default_parameter']:
            name_node = child.child_by_field_name('name') or child
            type_node = child.child_by_field_name('type')
            default_node = child.child_by_field_name('default') or child.child_by_field_name('value')
            name = get_node_text(name_node, code)
            type_name = get_node_text(type_node, code) if type_node else None
            default_val = get_node_text(default_node, code) if default_node else None
            if name not in ['self', 'cls', '(', ')', ',']:
                params.append({
                    'name': name,
                    'type': type_name,
                    'default': default_val
                })
    return params


def extract_function_calls(node, code):
    """Extract all function calls inside a function body"""
    calls = []

    def find_calls(n):
        if n.type in ['call', 'call_expression', 'function_call']:
            func_node = n.child_by_field_name('function') or (n.children[0] if n.children else None)
            if func_node:
                calls.append(get_node_text(func_node, code))
        for c in n.children:
            find_calls(c)

    find_calls(node)
    return list(set(calls))


def calculate_complexity(node):
    """Cyclomatic complexity simplified"""
    complexity = 1

    def count_branches(n):
        nonlocal complexity
        if n.type in ['if_statement', 'for_statement', 'while_statement',
                      'case_clause', 'catch_clause', 'conditional_expression']:
            complexity += 1
        for c in n.children:
            count_branches(c)

    count_branches(node)
    return complexity


# -------------------------------
# FUNCTION & CLASS EXTRACTION
# -------------------------------
def extract_function_info(node, code, language, file_name):
    # Determine function name
    name_node = node.child_by_field_name('name')
    if not name_node:
        # C function: identifier inside declarator
        declarator = node.child_by_field_name('declarator')
        if declarator:
            name_node = declarator.child_by_field_name('name') or declarator.child_by_field_name('identifier')
    func_name = get_node_text(name_node, code) if name_node else 'anonymous'

    param_node = node.child_by_field_name('parameters') or node.child_by_field_name('formal_parameters') or node.child_by_field_name('parameter_list')
    body_node = node.child_by_field_name('body')

    func_info = {
        'id': f"{file_name}_{func_name}_{node.start_point[0]}_{node.start_point[1]}",
        'name': func_name,
        'parameters': extract_parameters(param_node, code),
        'return_type': extract_return_type(node, code, language),
        'docstring': extract_docstring(node, code),
        'decorators': extract_decorators(node, code),
        'start_line': node.start_point[0] + 1,
        'end_line': node.end_point[0] + 1,
        'body': get_node_text(body_node, code) if body_node else '',
        'calls': extract_function_calls(node, code),
        'complexity': calculate_complexity(node),
        'is_async': 'async' in get_node_text(node, code)[:50],
        'language': language
    }
    return func_info


def extract_class_info(node, code, language, file_name):
    """Extract class info including methods and attributes"""
    name_node = node.child_by_field_name('name')
    superclass_node = node.child_by_field_name('superclass')

    methods = []
    body = node.child_by_field_name('body')
    if body:
        for child in body.children:
            if child.type in ['function_definition', 'method_declaration', 'method_definition']:
                method_info = extract_function_info(child, code, language, file_name)
                methods.append(method_info)

    # Attributes (Python style)
    attributes = []
    if language == 'py' and body:
        for child in body.children:
            text = get_node_text(child, code)
            if 'self.' in text and '=' in text:
                attr_name = text.split('self.')[1].split('=')[0].strip()
                attributes.append(attr_name)

    class_info = {
        'id': f"{file_name}_{name_node.start_point[0]}_{name_node.start_point[1]}" if name_node else 'anonymous',
        'name': get_node_text(name_node, code) if name_node else 'anonymous',
        'superclass': get_node_text(superclass_node, code) if superclass_node else None,
        'decorators': extract_decorators(node, code),
        'docstring': extract_docstring(node, code),
        'methods': methods,
        'attributes': list(set(attributes)),
        'start_line': node.start_point[0] + 1,
        'end_line': node.end_point[0] + 1,
        'language': language
    }
    return class_info


# -------------------------------
# AST TRAVERSAL
# -------------------------------
def traverse(node, code, language, ir, file_name, inside_class=None):
    """
    Recursively traverse AST to extract functions, classes, and variables.
    inside_class: None if top-level, else class name
    """
    # Function/method
    if node.type in ['function_definition', 'function_declaration', 'method_definition', 'method_declaration']:
        func_info = extract_function_info(node, code, language, file_name)
        
        # If inside a class, add to that class only
        if inside_class:
            # Include class name in ID for uniqueness
            func_info['id'] = f"{file_name}_{inside_class}_{func_info['name']}_{node.start_point[0]}_{node.start_point[1]}"
            ir['classes'][-1]['methods'].append(func_info)
        else:
            ir['functions'].append(func_info)

    # Class
    elif node.type in ['class_definition', 'class_declaration']:
        class_info = extract_class_info(node, code, language, file_name)
        ir['classes'].append(class_info)
        # Recurse children, marking the class name
        for c in node.children:
            traverse(c, code, language, ir, file_name, inside_class=class_info['name'])

    # Top-level variables
    elif node.type in ['variable_declarator', 'assignment'] and getattr(node.parent, 'type', None) == 'module':
        text = get_node_text(node, code)
        var_name = text.split('=')[0].strip() if '=' in text else text.strip()
        ir['variables'].append({
            'name': var_name,
            'line': node.start_point[0] + 1,
            'value': text.split('=')[1].strip() if '=' in text and len(text.split('=')) > 1 else None
        })

    for child in node.children:
        traverse(child, code, language, ir, file_name, inside_class)



# -------------------------------
# MAIN IR GENERATION
# -------------------------------
def generate_ir(source_dir: str, output_file: str = 'ir_output.json'):
    all_ir = []

    for filename in os.listdir(source_dir):
        file_path = os.path.join(source_dir, filename)
        ext = os.path.splitext(filename)[1]

        if ext in LANGUAGES and os.path.isfile(file_path):
            parser.set_language(LANGUAGES[ext])
            with open(file_path, 'rb') as f:
                code = f.read()

            tree = parser.parse(code)
            root_node = tree.root_node

            ir = {
                'file_name': filename,
                'file_path': file_path,
                'language': ext[1:],
                'imports': [],
                'functions': [],
                'classes': [],
                'variables': [],
                'total_lines': root_node.end_point[0] + 1
            }

            traverse(root_node, code, ext[1:], ir, filename)

            ir['stats'] = {
                'num_functions': len(ir['functions']),
                'num_classes': len(ir['classes']),
                'num_variables': len(ir['variables']),
                'has_docstrings': sum(1 for f in ir['functions'] if f['docstring']) +
                                 sum(1 for c in ir['classes'] if c['docstring'])
            }

            all_ir.append(ir)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_ir, f, indent=4)

    print(f"✅ IR generated for {len(all_ir)} files and saved to {output_file}")
    return all_ir


# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    ir_data = generate_ir(SOURCE_DIR)

    print("\n📊 IR Generation Summary:")
    for file_ir in ir_data:
        print(f"\n  {file_ir['file_name']} ({file_ir['language']}):")
        print(f"    Functions: {file_ir['stats']['num_functions']}")
        print(f"    Classes: {file_ir['stats']['num_classes']}")
        print(f"    With docstrings: {file_ir['stats']['has_docstrings']}")
