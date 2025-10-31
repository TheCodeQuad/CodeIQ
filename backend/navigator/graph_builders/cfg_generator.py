"""
CFG (Control Flow Graph) Generator using Python AST
Generates interactive HTML visualization using vis.js
"""
import ast
import json
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Fix encoding for Windows console
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class CFGNode:
    """Represents a node in the Control Flow Graph"""
    def __init__(self, node_id: int, node_type: str, label: str, line_no: int = None):
        self.id = node_id
        self.type = node_type  # 'entry', 'exit', 'statement', 'condition', 'loop'
        self.label = label
        self.line_no = line_no
        self.successors: List[int] = []
        
    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "line": self.line_no,
            "successors": self.successors
        }

class CFGBuilder(ast.NodeVisitor):
    """Builds Control Flow Graph from Python AST"""
    
    def __init__(self, function_name: str = "main"):
        self.function_name = function_name
        self.nodes: Dict[int, CFGNode] = {}
        self.edges: List[Tuple[int, int, str]] = []  # (from, to, label)
        self.node_counter = 0
        self.current_block = None
        self.break_targets: List[int] = []
        self.continue_targets: List[int] = []
        
    def new_node(self, node_type: str, label: str, line_no: int = None) -> CFGNode:
        """Create a new CFG node"""
        node = CFGNode(self.node_counter, node_type, label, line_no)
        self.nodes[self.node_counter] = node
        self.node_counter += 1
        return node
    
    def add_edge(self, from_node: int, to_node: int, label: str = ""):
        """Add an edge between two nodes"""
        if from_node is not None and to_node is not None:
            if to_node not in self.nodes[from_node].successors:
                self.nodes[from_node].successors.append(to_node)
                self.edges.append((from_node, to_node, label))
    
    def build_cfg(self, source_code: str) -> Dict:
        """Main method to build CFG from source code"""
        try:
            tree = ast.parse(source_code)
            
            # Create entry node
            entry = self.new_node("entry", f"START: {self.function_name}", 1)
            self.current_block = entry.id
            
            # Visit all statements
            for stmt in tree.body:
                self.current_block = self.visit_statement(stmt, self.current_block)
            
            # Create exit node
            exit_node = self.new_node("exit", f"END: {self.function_name}", None)
            if self.current_block is not None:
                self.add_edge(self.current_block, exit_node.id)
            
            return self.to_dict()
            
        except SyntaxError as e:
            return {"error": f"Syntax error: {str(e)}", "nodes": [], "edges": []}
    
    def visit_statement(self, stmt, current: int) -> int:
        """Visit a statement and return the next block ID"""
        if isinstance(stmt, ast.FunctionDef):
            return self.visit_FunctionDef(stmt, current)
        elif isinstance(stmt, ast.If):
            return self.visit_If(stmt, current)
        elif isinstance(stmt, (ast.While, ast.For)):
            return self.visit_Loop(stmt, current)
        elif isinstance(stmt, ast.Return):
            return self.visit_Return(stmt, current)
        elif isinstance(stmt, ast.Break):
            return self.visit_Break(stmt, current)
        elif isinstance(stmt, ast.Continue):
            return self.visit_Continue(stmt, current)
        elif isinstance(stmt, ast.Try):
            return self.visit_Try(stmt, current)
        else:
            return self.visit_SimpleStatement(stmt, current)
    
    def visit_FunctionDef(self, node: ast.FunctionDef, current: int) -> int:
        """Handle function definition"""
        func_node = self.new_node("statement", f"def {node.name}(...)", node.lineno)
        self.add_edge(current, func_node.id)
        
        # Process function body
        body_current = func_node.id
        for stmt in node.body:
            body_current = self.visit_statement(stmt, body_current)
        
        return body_current
    
    def visit_If(self, node: ast.If, current: int) -> int:
        """Handle if-elif-else statements"""
        # Condition node
        condition_text = ast.unparse(node.test) if hasattr(ast, 'unparse') else "condition"
        if len(condition_text) > 40:
            condition_text = condition_text[:37] + "..."
        cond_node = self.new_node("condition", f"if {condition_text}", node.lineno)
        self.add_edge(current, cond_node.id)
        
        # True branch
        true_current = cond_node.id
        for stmt in node.body:
            true_current = self.visit_statement(stmt, true_current)
        
        # False branch (else/elif)
        false_current = cond_node.id
        if node.orelse:
            for stmt in node.orelse:
                false_current = self.visit_statement(stmt, false_current)
        
        # Merge node
        merge_node = self.new_node("statement", "merge", None)
        if true_current is not None:
            self.add_edge(true_current, merge_node.id, "true")
        if false_current is not None and false_current != cond_node.id:
            self.add_edge(false_current, merge_node.id, "false")
        elif false_current == cond_node.id:
            self.add_edge(cond_node.id, merge_node.id, "false")
        
        return merge_node.id
    
    def visit_Loop(self, node, current: int) -> int:
        """Handle while and for loops"""
        if isinstance(node, ast.While):
            loop_type = "while"
            condition_text = ast.unparse(node.test) if hasattr(ast, 'unparse') else "condition"
        else:  # For loop
            loop_type = "for"
            target = ast.unparse(node.target) if hasattr(ast, 'unparse') else "var"
            iter_text = ast.unparse(node.iter) if hasattr(ast, 'unparse') else "iterable"
            condition_text = f"{target} in {iter_text}"
        
        if len(condition_text) > 40:
            condition_text = condition_text[:37] + "..."
        
        # Loop header
        loop_node = self.new_node("loop", f"{loop_type} {condition_text}", node.lineno)
        self.add_edge(current, loop_node.id)
        
        # Exit node for the loop
        exit_node = self.new_node("statement", f"end {loop_type}", None)
        
        # Track break/continue targets
        self.break_targets.append(exit_node.id)
        self.continue_targets.append(loop_node.id)
        
        # Loop body
        body_current = loop_node.id
        for stmt in node.body:
            body_current = self.visit_statement(stmt, body_current)
        
        # Back edge to loop header
        if body_current is not None:
            self.add_edge(body_current, loop_node.id, "loop")
        
        # Exit edge
        self.add_edge(loop_node.id, exit_node.id, "exit")
        
        # Pop break/continue targets
        self.break_targets.pop()
        self.continue_targets.pop()
        
        return exit_node.id
    
    def visit_Return(self, node: ast.Return, current: int) -> int:
        """Handle return statements"""
        value = ast.unparse(node.value) if node.value and hasattr(ast, 'unparse') else ""
        if len(value) > 30:
            value = value[:27] + "..."
        ret_node = self.new_node("statement", f"return {value}", node.lineno)
        self.add_edge(current, ret_node.id)
        return None  # No successor after return
    
    def visit_Break(self, node: ast.Break, current: int) -> int:
        """Handle break statements"""
        break_node = self.new_node("statement", "break", node.lineno)
        self.add_edge(current, break_node.id)
        if self.break_targets:
            self.add_edge(break_node.id, self.break_targets[-1], "break")
        return None
    
    def visit_Continue(self, node: ast.Continue, current: int) -> int:
        """Handle continue statements"""
        cont_node = self.new_node("statement", "continue", node.lineno)
        self.add_edge(current, cont_node.id)
        if self.continue_targets:
            self.add_edge(cont_node.id, self.continue_targets[-1], "continue")
        return None
    
    def visit_Try(self, node: ast.Try, current: int) -> int:
        """Handle try-except blocks"""
        try_node = self.new_node("statement", "try", node.lineno)
        self.add_edge(current, try_node.id)
        
        # Try block
        try_current = try_node.id
        for stmt in node.body:
            try_current = self.visit_statement(stmt, try_current)
        
        # Except handlers
        except_exits = []
        for handler in node.handlers:
            exc_type = "Exception"
            if handler.type:
                if hasattr(handler.type, 'id'):
                    exc_type = handler.type.id
                elif hasattr(ast, 'unparse'):
                    exc_type = ast.unparse(handler.type)
            
            except_node = self.new_node("statement", f"except {exc_type}", handler.lineno)
            self.add_edge(try_node.id, except_node.id, "exception")
            
            except_current = except_node.id
            for stmt in handler.body:
                except_current = self.visit_statement(stmt, except_current)
            except_exits.append(except_current)
        
        # Merge node
        merge_node = self.new_node("statement", "end try", None)
        if try_current is not None:
            self.add_edge(try_current, merge_node.id)
        for exit_id in except_exits:
            if exit_id is not None:
                self.add_edge(exit_id, merge_node.id)
        
        return merge_node.id
    
    def visit_SimpleStatement(self, stmt, current: int) -> int:
        """Handle simple statements"""
        label = ast.unparse(stmt) if hasattr(ast, 'unparse') else type(stmt).__name__
        # Truncate long statements
        if len(label) > 50:
            label = label[:47] + "..."
        
        stmt_node = self.new_node("statement", label, getattr(stmt, 'lineno', None))
        self.add_edge(current, stmt_node.id)
        return stmt_node.id
    
    def to_dict(self) -> Dict:
        """Convert CFG to dictionary format"""
        return {
            "function": self.function_name,
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [{"from": f, "to": t, "label": l} for f, t, l in self.edges]
        }

def build_cfg_for_file(file_path: str) -> Dict:
    """Build CFG for all functions in a Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    # Parse the file to find all functions
    tree = ast.parse(source)
    cfgs = {}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Extract function source
            func_lines = source.split('\n')[node.lineno - 1:node.end_lineno]
            func_source = '\n'.join(func_lines)
            
            builder = CFGBuilder(node.name)
            cfg = builder.build_cfg(func_source)
            cfgs[node.name] = cfg
    
    # If no functions, build CFG for entire file
    if not cfgs:
        builder = CFGBuilder("module")
        cfgs["module"] = builder.build_cfg(source)
    
    return {
        "file": os.path.basename(file_path),
        "functions": cfgs
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cfg_generator.py <python_file> [output_json]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "cfg_output.json"
    
    print(f"Building CFG for {input_file}...")
    result = build_cfg_for_file(input_file)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"✅ CFG saved to {output_file}")
