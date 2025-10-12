import json
import networkx as nx
import matplotlib.pyplot as plt
from tree_sitter import Language, Parser

class MultiLanguageCFGGenerator:
    def __init__(self):
        self.parser = Parser()
        # Load your existing language
        MY_LANG = 'build/my-languages.so'
        self.LANGUAGES = {
            'py': Language(MY_LANG, 'python'),
            'java': Language(MY_LANG, 'java'),
            'js': Language(MY_LANG, 'javascript'),
            'c': Language(MY_LANG, 'c'),
        }
        
    def get_node_text(self, node, code):
        return code[node.start_byte:node.end_byte].decode('utf-8')
    
    def set_language(self, file_extension):
        """Set parser language based on file extension"""
        lang = self.LANGUAGES.get(file_extension)
        if lang:
            self.parser.set_language(lang)
        return lang

    def find_function_nodes(self, root_node, code, language):
        """Find all function/method nodes based on language"""
        functions = []
        
        def traverse(node):
            # Language-specific function detection
            if language == 'py':
                if node.type == 'function_definition':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        func_name = self.get_node_text(name_node, code)
                        functions.append(('function', func_name, node))
                
                elif node.type == 'class_definition':
                    name_node = node.child_by_field_name('name')
                    class_name = self.get_node_text(name_node, code) if name_node else 'anonymous'
                    
                    # Find methods in class
                    body = node.child_by_field_name('body')
                    if body:
                        for child in body.children:
                            if child.type == 'function_definition':
                                method_name_node = child.child_by_field_name('name')
                                if method_name_node:
                                    method_name = self.get_node_text(method_name_node, code)
                                    functions.append(('method', f"{class_name}.{method_name}", child))
            
            elif language == 'java':
                if node.type in ['method_declaration', 'constructor_declaration']:
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        method_name = self.get_node_text(name_node, code)
                        # Find containing class
                        class_node = self._find_parent_class(node)
                        if class_node:
                            class_name_node = class_node.child_by_field_name('name')
                            class_name = self.get_node_text(class_name_node, code) if class_name_node else 'anonymous'
                            functions.append(('method', f"{class_name}.{method_name}", node))
                        else:
                            functions.append(('function', method_name, node))
                
                elif node.type == 'class_declaration':
                    name_node = node.child_by_field_name('name')
                    class_name = self.get_node_text(name_node, code) if name_node else 'anonymous'
                    functions.append(('class', class_name, node))
            
            elif language == 'js':
                if node.type in ['function_declaration', 'function']:
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        func_name = self.get_node_text(name_node, code)
                        functions.append(('function', func_name, node))
                
                elif node.type == 'method_definition':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        method_name = self.get_node_text(name_node, code)
                        # Find containing class
                        class_node = self._find_parent_class(node)
                        if class_node:
                            class_name_node = class_node.child_by_field_name('name')
                            class_name = self.get_node_text(class_name_node, code) if class_name_node else 'anonymous'
                            functions.append(('method', f"{class_name}.{method_name}", node))
                
                elif node.type == 'class_declaration':
                    name_node = node.child_by_field_name('name')
                    class_name = self.get_node_text(name_node, code) if name_node else 'anonymous'
                    functions.append(('class', class_name, node))
            
            elif language == 'c':
                if node.type == 'function_definition':
                    declarator = node.child_by_field_name('declarator')
                    if declarator:
                        name_node = declarator.child_by_field_name('name') or declarator.child_by_field_name('declarator')
                        if name_node:
                            func_name = self.get_node_text(name_node, code)
                            functions.append(('function', func_name, node))
                
                elif node.type == 'declaration':
                    # Check if it's a function declaration
                    for child in node.children:
                        if child.type == 'function_declarator':
                            name_node = child.child_by_field_name('name')
                            if name_node:
                                func_name = self.get_node_text(name_node, code)
                                functions.append(('function', func_name, node))
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return functions

    def _find_parent_class(self, node):
        """Find the parent class node"""
        current = node.parent
        while current:
            if current.type in ['class_declaration', 'class_definition']:
                return current
            current = current.parent
        return None

    def build_cfg_for_function(self, function_node, code, function_name, language):
        """Build CFG for a single function with language-specific handling"""
        cfg = nx.DiGraph()
        
        # Get function body based on language
        body_node = None
        if language == 'py':
            body_node = function_node.child_by_field_name('body')
        elif language in ['java', 'js', 'c']:
            body_node = function_node.child_by_field_name('body')
            if not body_node:
                # For some languages, body might be called 'compound_statement' or similar
                for child in function_node.children:
                    if child.type in ['block', 'compound_statement']:
                        body_node = child
                        break
        
        if not body_node:
            print(f"    ⚠️  No body found for {function_name}")
            return cfg
        
        basic_blocks = self._extract_basic_blocks(body_node, code, language)
        self._create_cfg_from_blocks(cfg, basic_blocks, code, function_name)
        
        return cfg

    def _extract_basic_blocks(self, body_node, code, language):
        """Extract basic blocks from function body"""
        basic_blocks = []
        current_block = []
        
        def traverse_blocks(node):
            nonlocal current_block
            
            # Statements that typically start new basic blocks
            block_starters = [
                'if_statement', 'while_statement', 'for_statement', 
                'return_statement', 'break_statement', 'continue_statement'
            ]
            
            # Language-specific additions
            if language == 'java':
                block_starters.extend(['switch_statement', 'try_statement'])
            elif language == 'c':
                block_starters.extend(['switch_statement', 'case_statement', 'goto_statement'])
            
            if node.type in block_starters:
                if current_block:
                    basic_blocks.append(current_block)
                    current_block = []
            
            # Add executable statements to current block
            executable_types = [
                'expression_statement', 'assignment', 'return_statement',
                'augmented_assignment', 'break_statement', 'continue_statement'
            ]
            
            if language == 'java':
                executable_types.extend(['local_variable_declaration', 'method_invocation'])
            elif language == 'c':
                executable_types.extend(['declaration', 'expression_statement'])
            
            if node.type in executable_types:
                current_block.append(node)
            
            # Recursively process children
            for child in node.children:
                traverse_blocks(child)
        
        traverse_blocks(body_node)
        
        # Add the last block
        if current_block:
            basic_blocks.append(current_block)
        
        return basic_blocks

    def _create_cfg_from_blocks(self, cfg, basic_blocks, code, function_name):
        """Create CFG nodes from basic blocks"""
        if not basic_blocks:
            return
        
        # Add entry node
        cfg.add_node("entry", label=f"Entry\n{function_name}", type="entry")
        
        # Add basic block nodes
        for i, block in enumerate(basic_blocks):
            if block:
                block_id = f"block_{i}"
                block_label = self._create_block_label(block, code)
                cfg.add_node(block_id, label=block_label, type="basic_block")
        
        # Connect blocks sequentially (simplified - you can enhance with proper control flow)
        if basic_blocks:
            first_block = "block_0"
            cfg.add_edge("entry", first_block)
            
            for i in range(len(basic_blocks) - 1):
                if basic_blocks[i]:
                    cfg.add_edge(f"block_{i}", f"block_{i+1}")
        
        # Add exit node
        cfg.add_node("exit", label="Exit", type="exit")
        if basic_blocks:
            last_block = f"block_{len(basic_blocks)-1}"
            cfg.add_edge(last_block, "exit")

    def _create_block_label(self, block, code):
        """Create label for a basic block"""
        lines = []
        for node in block:
            if node:
                text = self.get_node_text(node, code)
                # Clean and truncate
                text = ' '.join(text.split())[:30] + "..." if len(text) > 30 else text
                lines.append(text)
        return "\n".join(lines) if lines else "Empty Block"

    def visualize_cfg(self, cfg, function_name, output_file=None):
        """Visualize a single CFG"""
        if cfg.number_of_nodes() == 0:
            print(f"    ⚠️  Empty CFG for {function_name}, skipping visualization")
            return
        
        plt.figure(figsize=(10, 8))
        
        pos = nx.spring_layout(cfg, k=1, iterations=50)
        
        # Color nodes by type
        node_colors = []
        node_sizes = []
        for node in cfg.nodes():
            node_type = cfg.nodes[node].get('type', 'basic_block')
            if node_type == 'entry':
                node_colors.append('#90EE90')  # Light green
                node_sizes.append(1500)
            elif node_type == 'exit':
                node_colors.append('#FFB6C1')  # Light red
                node_sizes.append(1500)
            else:
                node_colors.append('#87CEEB')  # Light blue
                node_sizes.append(2000)
        
        # Draw the graph
        nx.draw_networkx_nodes(cfg, pos, node_color=node_colors, 
                              node_size=node_sizes, alpha=0.9)
        nx.draw_networkx_edges(cfg, pos, arrows=True, arrowsize=20,
                              edge_color='gray', alpha=0.7)
        
        # Draw labels
        labels = {node: cfg.nodes[node]['label'] for node in cfg.nodes()}
        nx.draw_networkx_labels(cfg, pos, labels, font_size=8)
        
        plt.title(f"Control Flow Graph: {function_name}", size=12)
        plt.axis('off')
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"    ✅ CFG saved as {output_file}")
        
        plt.show()

# -------------------------------
# MAIN CFG GENERATION - FIXED
# -------------------------------

def generate_cfgs_from_ir_fixed(ir_file='ir_output.json', output_dir='cfgs'):
    """Generate CFGs for all functions in the IR - Fixed version"""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Load IR data
    with open(ir_file, 'r') as f:
        ir_data = json.load(f)
    
    cfg_generator = MultiLanguageCFGGenerator()
    all_cfgs = {}
    
    print("🔧 Generating Control Flow Graphs...")
    
    for file_ir in ir_data:
        filename = file_ir['file_name']
        file_ext = os.path.splitext(filename)[1][1:]  # Remove dot
        file_path = file_ir.get('file_path', os.path.join('../source_files', filename))
        
        print(f"\n📁 Processing {filename} ({file_ext})")
        
        # Set language for parser
        if not cfg_generator.set_language(file_ext):
            print(f"    ❌ Unsupported language: {file_ext}")
            continue
        
        # Read source code
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()
        except FileNotFoundError:
            print(f"    ❌ File not found: {file_path}")
            continue
        
        # Parse and find all functions
        tree = cfg_generator.parser.parse(source_code)
        functions = cfg_generator.find_function_nodes(tree.root_node, source_code, file_ext)
        
        print(f"    Found {len(functions)} functions/methods")
        
        # Generate CFG for each function
        for func_type, func_name, func_node in functions:
            print(f"    🔹 Generating CFG for {func_type}: {func_name}")
            
            try:
                cfg = cfg_generator.build_cfg_for_function(
                    func_node, source_code, func_name, file_ext
                )
                
                # Visualize if CFG has content
                if cfg.number_of_nodes() > 0:
                    output_file = os.path.join(
                        output_dir, 
                        f"cfg_{filename}_{func_name}.png".replace('/', '_').replace('.', '_')
                    )
                    cfg_generator.visualize_cfg(cfg, func_name, output_file)
                    
                    all_cfgs[f"{filename}_{func_name}"] = cfg
                else:
                    print(f"    ⚠️  Empty CFG for {func_name}")
                    
            except Exception as e:
                print(f"    ❌ Error generating CFG for {func_name}: {str(e)}")
    
    print(f"\n✅ Generated {len(all_cfgs)} CFGs in '{output_dir}' directory")
    return all_cfgs

# -------------------------------
# DEBUGGING TOOL
# -------------------------------

def debug_ast_structure(ir_file='ir_output.json'):
    """Debug AST structure to understand node types"""
    import os
    from tree_sitter import Parser, Language
    
    MY_LANG = 'build/my-languages.so'
    LANGUAGES = {
        'java': Language(MY_LANG, 'java'),
        'js': Language(MY_LANG, 'javascript'),
        'c': Language(MY_LANG, 'c'),
        'py': Language(MY_LANG, 'python'),
    }
    
    parser = Parser()
    
    with open(ir_file, 'r') as f:
        ir_data = json.load(f)
    
    for file_ir in ir_data:
        filename = file_ir['file_name']
        file_ext = os.path.splitext(filename)[1][1:]
        file_path = file_ir.get('file_path', os.path.join('../source_files', filename))
        
        print(f"\n🔍 Debugging {filename} ({file_ext}):")
        
        if file_ext not in LANGUAGES:
            print("    ❌ Unsupported language")
            continue
        
        parser.set_language(LANGUAGES[file_ext])
        
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()
        except FileNotFoundError:
            print("    ❌ File not found")
            continue
        
        tree = parser.parse(source_code)
        
        # Print all node types in the AST
        def print_node_types(node, depth=0):
            indent = "    " * depth
            print(f"{indent}{node.type}")
            if depth < 3:  # Limit depth for readability
                for child in node.children:
                    print_node_types(child, depth + 1)
        
        print("    AST Structure:")
        print_node_types(tree.root_node)

# -------------------------------
# SIMPLE TEST WITH SAMPLE CODE
# -------------------------------

def test_with_sample_code():
    """Test CFG generation with sample code snippets"""
    cfg_generator = MultiLanguageCFGGenerator()
    
    # Test with Python
    print("Testing with Python code...")
    python_code = """
def test_function(x):
    if x > 0:
        print("Positive")
        return 1
    else:
        print("Non-positive")
        return 0
    print("End")
""".encode('utf-8')
    
    cfg_generator.set_language('py')
    tree = cfg_generator.parser.parse(python_code)
    functions = cfg_generator.find_function_nodes(tree.root_node, python_code, 'py')
    
    for func_type, func_name, func_node in functions:
        print(f"Found {func_type}: {func_name}")
        cfg = cfg_generator.build_cfg_for_function(func_node, python_code, func_name, 'py')
        cfg_generator.visualize_cfg(cfg, func_name)

# -------------------------------
# MAIN EXECUTION
# -------------------------------

if __name__ == "__main__":
    print("🎯 CFG Generation Started")
    
    # Option 1: Debug AST structure first
    print("\n1. 🔍 Debugging AST structure...")
    debug_ast_structure()
    
    # Option 2: Test with sample code
    print("\n2. 🧪 Testing with sample code...")
    test_with_sample_code()
    
    # Option 3: Generate CFGs from IR
    print("\n3. 🏗️ Generating CFGs from IR...")
    all_cfgs = generate_cfgs_from_ir_fixed()
    
    print(f"\n🎉 Completed! Generated {len(all_cfgs)} CFGs")