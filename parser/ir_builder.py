import os
from tree_sitter import Language, Parser
from dataclasses import dataclass, field
from typing import List

# -----------------------------
# Load Tree-sitter Languages
# -----------------------------
LANG_SO = 'build/my-languages.so'
LANG_MAP = {
    'c': Language(LANG_SO, 'c'),
    'java': Language(LANG_SO, 'java'),
    'python': Language(LANG_SO, 'python'),
    'javascript': Language(LANG_SO, 'javascript')
}

# -----------------------------
# IR Node
# -----------------------------
@dataclass
class IRNode:
    type: str
    name: str = None
    parameters: List[str] = field(default_factory=list)
    lhs: str = None
    rhs: str = None
    defines: List[str] = field(default_factory=list)
    uses: List[str] = field(default_factory=list)
    children: List['IRNode'] = field(default_factory=list)

    def to_dict(self):
        return {
            "type": self.type,
            "name": self.name,
            "parameters": self.parameters,
            "lhs": self.lhs,
            "rhs": self.rhs,
            "defines": self.defines,
            "uses": self.uses,
            "children": [child.to_dict() for child in self.children]
        }

# -----------------------------
# Language-specific Node Maps
# -----------------------------
FUNC_NODES = {
    'c': ['function_definition'],
    'java': ['method_declaration'],
    'python': ['function_definition'],
    'javascript': ['function_declaration', 'method_definition']
}

CLASS_NODES = {
    'c': ['struct_specifier'],  
    'java': ['class_declaration'],
    'python': ['class_definition'],
    'javascript': ['class_declaration']
}

ASSIGN_NODES = {
    'python': ['assignment'],
    'javascript': ['assignment_expression'],
    'java': ['local_variable_declaration'],
    'c': ['assignment_expression']
}

RETURN_NODES = {
    'python': ['return_statement'],
    'javascript': ['return_statement'],
    'java': ['return_statement'],
    'c': ['return_statement']
}

COND_NODES = {
    'python': ['if_statement', 'for_statement', 'while_statement'],
    'javascript': ['if_statement', 'for_statement', 'while_statement'],
    'java': ['if_statement', 'for_statement', 'while_statement'],
    'c': ['if_statement', 'for_statement', 'while_statement']
}

# -----------------------------
# Build IR recursively
# -----------------------------
def get_node_text(node, source_code):
    return source_code[node.start_byte:node.end_byte].decode('utf-8')

def build_ir(node, lang, source_code):
    # Functions / Methods
    if node.type in FUNC_NODES[lang]:
        name_node = None
        for child in node.children:
            if child.type == 'identifier':
                name_node = child
                break
        name = get_node_text(name_node, source_code) if name_node else None
        # Parameters
        params = []
        param_field = node.child_by_field_name('parameters')
        if param_field:
            for p in param_field.children:
                if p.type == 'identifier':
                    params.append(get_node_text(p, source_code))
        ir_node = IRNode(type='function', name=name, parameters=params)
        for child in node.children:
            ir_node.children.append(build_ir(child, lang, source_code))
        return ir_node

    # Classes
    elif node.type in CLASS_NODES[lang]:
        name_node = node.child_by_field_name('name')
        name = get_node_text(name_node, source_code) if name_node else None
        ir_node = IRNode(type='class', name=name)
        for child in node.children:
            ir_node.children.append(build_ir(child, lang, source_code))
        return ir_node

    # Assignment statements
    elif node.type in ASSIGN_NODES.get(lang, []):
        lhs, rhs = None, None
        defines, uses = [], []
        if len(node.children) >= 3:
            lhs = get_node_text(node.children[0], source_code)
            rhs = get_node_text(node.children[2], source_code)
            defines.append(lhs)
            # Simple variable extraction from rhs (improve later)
            for child in node.children[2].children:
                if child.type == 'identifier':
                    uses.append(get_node_text(child, source_code))
        return IRNode(type='assignment', lhs=lhs, rhs=rhs, defines=defines, uses=uses)

    # Return statements
    elif node.type in RETURN_NODES.get(lang, []):
        expr = None
        uses = []
        if node.child_by_field_name('argument'):
            expr_node = node.child_by_field_name('argument')
            expr = get_node_text(expr_node, source_code)
            # Collect used identifiers
            for child in expr_node.children:
                if child.type == 'identifier':
                    uses.append(get_node_text(child, source_code))
        return IRNode(type='return_statement', rhs=expr, uses=uses)

    # Conditional / loops
    elif node.type in COND_NODES.get(lang, []):
        ir_node = IRNode(type=node.type)
        for child in node.children:
            ir_node.children.append(build_ir(child, lang, source_code))
        return ir_node

    # Generic node
    ir_node = IRNode(type=node.type)
    for child in node.children:
        ir_node.children.append(build_ir(child, lang, source_code))
    return ir_node

# -----------------------------
# Parse a file and build IR
# -----------------------------
def parse_file(file_path, lang):
    parser = Parser()
    parser.set_language(LANG_MAP[lang])
    with open(file_path, 'rb') as f:
        source_code = f.read()
    tree = parser.parse(source_code)
    root = tree.root_node
    return build_ir(root, lang, source_code)

# -----------------------------
# Detect language from extension
# -----------------------------
EXT_LANG = {
    '.c': 'c',
    '.java': 'java',
    '.py': 'python',
    '.js': 'javascript'
}

def detect_language(file_path):
    ext = os.path.splitext(file_path)[1]
    return EXT_LANG.get(ext, None)
