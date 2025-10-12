import json
import networkx as nx
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import matplotlib.pyplot as plt
with open("ir_output.json", "r") as f:
    ir_data = json.load(f)

# ============================================================================
# DATA STRUCTURES
# ============================================================================

class NodeType(Enum):
    """Types of nodes in different graphs"""
    # HPG Node Types
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    
    # CFG Node Types
    ENTRY = "entry"
    EXIT = "exit"
    STATEMENT = "statement"
    CONDITION = "condition"
    LOOP = "loop"
    
    # PDG Node Types
    DATA = "data"
    CONTROL = "control"

class EdgeType(Enum):
    """Types of edges in different graphs"""
    # HPG Edges
    CONTAINS = "contains"
    
    # CFG Edges
    SEQUENTIAL = "sequential"
    CONDITIONAL_TRUE = "conditional_true"
    CONDITIONAL_FALSE = "conditional_false"
    LOOP_BACK = "loop_back"
    
    # PDG Edges
    DATA_DEPENDENCY = "data_dependency"
    CONTROL_DEPENDENCY = "control_dependency"
    CALL = "call"

@dataclass
class GraphNode:
    """Generic graph node"""
    id: str
    type: NodeType
    name: str
    metadata: Dict[str, Any]

# ============================================================================
# HIERARCHICAL PROGRAM GRAPH (HPG) BUILDER
# ============================================================================

class HPGBuilder:
    """Builds Hierarchical Program Graph showing code structure"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.node_counter = 0
    
    def build(self, ir_data: List[Dict]) -> nx.DiGraph:
        """Build HPG from IR data"""
        print("🔨 Building Hierarchical Program Graph (HPG)...")
        
        for file_ir in ir_data:
            # Create module node
            module_id = self._create_node(
                NodeType.MODULE,
                file_ir['file_name'],
                {
                    'language': file_ir['language'],
                    'path': file_ir['file_path'],
                    'total_lines': file_ir['total_lines']
                }
            )
            
            # Add classes
            for class_info in file_ir['classes']:
                class_id = self._create_node(
                    NodeType.CLASS,
                    class_info['name'],
                    {
                        'docstring': class_info['docstring'],
                        'superclass': class_info['superclass'],
                        'start_line': class_info['start_line'],
                        'end_line': class_info['end_line']
                    }
                )
                self.graph.add_edge(module_id, class_id, type=EdgeType.CONTAINS.value)
                
                # Add methods to class
                for method in class_info['methods']:
                    method_id = self._create_node(
                        NodeType.METHOD,
                        method['name'],
                        {
                            'parameters': method['parameters'],
                            'return_type': method['return_type'],
                            'complexity': method['complexity'],
                            'start_line': method['start_line'],
                            'end_line': method['end_line'],
                            'is_async': method['is_async']
                        }
                    )
                    self.graph.add_edge(class_id, method_id, type=EdgeType.CONTAINS.value)
            
            # Add standalone functions
            for func_info in file_ir['functions']:
                # Skip methods (already added)
                if not any(func_info['name'] == m['name'] 
                          for c in file_ir['classes'] 
                          for m in c['methods']):
                    func_id = self._create_node(
                        NodeType.FUNCTION,
                        func_info['name'],
                        {
                            'parameters': func_info['parameters'],
                            'return_type': func_info['return_type'],
                            'complexity': func_info['complexity'],
                            'calls': func_info['calls'],
                            'start_line': func_info['start_line'],
                            'end_line': func_info['end_line'],
                            'is_async': func_info['is_async']
                        }
                    )
                    self.graph.add_edge(module_id, func_id, type=EdgeType.CONTAINS.value)
        
        print(f"✅ HPG built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        return self.graph
    
    def _create_node(self, node_type: NodeType, name: str, metadata: Dict) -> str:
        """Create a node and return its ID"""
        node_id = f"{node_type.value}_{self.node_counter}"
        self.node_counter += 1
        
        self.graph.add_node(
            node_id,
            type=node_type.value,
            name=name,
            **metadata
        )
        return node_id
    
    def get_hierarchy(self, node_id: str) -> List[str]:
        """Get hierarchical path to a node"""
        ancestors = list(nx.ancestors(self.graph, node_id))
        ancestors.append(node_id)
        return ancestors
    
    def export_to_json(self, filename: str = "hpg.json"):
        """Export HPG to JSON"""
        data = nx.node_link_data(self.graph)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 HPG exported to {filename}")

# ============================================================================
# CONTROL FLOW GRAPH (CFG) BUILDER
# ============================================================================

class CFGBuilder:
    """Builds Control Flow Graph for each function"""
    
    def __init__(self):
        self.graphs = {}  # function_id -> CFG
    
    def build(self, ir_data: List[Dict]) -> Dict[str, nx.DiGraph]:
        """Build CFG for all functions"""
        print("🔨 Building Control Flow Graphs (CFG)...")
        
        for file_ir in ir_data:
            # Build CFG for standalone functions
            for func_info in file_ir['functions']:
                func_id = func_info['id']
                cfg = self._build_function_cfg(func_info)
                self.graphs[func_id] = cfg
            
            # Build CFG for class methods
            for class_info in file_ir['classes']:
                for method in class_info['methods']:
                    method_id = method['id']
                    cfg = self._build_function_cfg(method)
                    self.graphs[method_id] = cfg
        
        print(f"✅ CFG built for {len(self.graphs)} functions")
        return self.graphs
    
    def _build_function_cfg(self, func_info: Dict) -> nx.DiGraph:
        """Build CFG for a single function"""
        cfg = nx.DiGraph()
        body = func_info['body']
        
        # Create entry and exit nodes
        entry_id = f"{func_info['id']}_entry"
        exit_id = f"{func_info['id']}_exit"
        
        cfg.add_node(entry_id, type=NodeType.ENTRY.value, label="ENTRY")
        cfg.add_node(exit_id, type=NodeType.EXIT.value, label="EXIT")
        
        # Parse function body to build control flow
        # This is simplified - you'd need proper AST traversal for accuracy
        statements = self._extract_statements(body)
        
        if not statements:
            cfg.add_edge(entry_id, exit_id, type=EdgeType.SEQUENTIAL.value)
            return cfg
        
        prev_node = entry_id
        
        for i, stmt in enumerate(statements):
            stmt_id = f"{func_info['id']}_stmt_{i}"
            stmt_type = self._classify_statement(stmt)
            
            cfg.add_node(
                stmt_id,
                type=stmt_type.value,
                label=stmt['text'][:50],  # Truncate long statements
                line=stmt['line']
            )
            
            # Handle different statement types
            if stmt_type == NodeType.CONDITION:
                # Conditional branching
                true_branch = f"{func_info['id']}_stmt_{i+1}"
                false_branch = f"{func_info['id']}_stmt_{i+2}"
                
                cfg.add_edge(prev_node, stmt_id, type=EdgeType.SEQUENTIAL.value)
                # In reality, you'd parse the actual branches
                prev_node = stmt_id
                
            elif stmt_type == NodeType.LOOP:
                # Loop back edge
                cfg.add_edge(prev_node, stmt_id, type=EdgeType.SEQUENTIAL.value)
                # Loop body would create a back edge
                prev_node = stmt_id
                
            else:
                # Regular sequential flow
                cfg.add_edge(prev_node, stmt_id, type=EdgeType.SEQUENTIAL.value)
                prev_node = stmt_id
        
        # Connect last statement to exit
        cfg.add_edge(prev_node, exit_id, type=EdgeType.SEQUENTIAL.value)
        
        return cfg
    
    def _extract_statements(self, body: str) -> List[Dict]:
        """Extract statements from function body (simplified)"""
        statements = []
        lines = body.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line.startswith('#'):
                statements.append({
                    'text': line,
                    'line': i + 1
                })
        
        return statements
    
    def _classify_statement(self, stmt: Dict) -> NodeType:
        """Classify statement type"""
        text = stmt['text'].lower()
        
        if any(kw in text for kw in ['if ', 'elif ', 'else:', 'switch', 'case']):
            return NodeType.CONDITION
        elif any(kw in text for kw in ['for ', 'while ', 'do ']):
            return NodeType.LOOP
        else:
            return NodeType.STATEMENT
    
    def get_cfg(self, function_id: str) -> nx.DiGraph:
        """Get CFG for a specific function"""
        return self.graphs.get(function_id)
    
    def export_to_json(self, filename: str = "cfg.json"):
        """Export all CFGs to JSON"""
        data = {
            func_id: nx.node_link_data(cfg)
            for func_id, cfg in self.graphs.items()
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 CFG exported to {filename}")

# ============================================================================
# PROGRAM DEPENDENCY GRAPH (PDG) BUILDER
# ============================================================================

class PDGBuilder:
    """Builds Program Dependency Graph showing data and control dependencies"""
    
    def __init__(self):
        self.graphs = {}  # function_id -> PDG
    
    def build(self, ir_data: List[Dict], cfg_graphs: Dict[str, nx.DiGraph]) -> Dict[str, nx.DiGraph]:
        """Build PDG for all functions"""
        print("🔨 Building Program Dependency Graphs (PDG)...")
        
        for file_ir in ir_data:
            # Build PDG for standalone functions
            for func_info in file_ir['functions']:
                func_id = func_info['id']
                cfg = cfg_graphs.get(func_id)
                if cfg:
                    pdg = self._build_function_pdg(func_info, cfg)
                    self.graphs[func_id] = pdg
            
            # Build PDG for class methods
            for class_info in file_ir['classes']:
                for method in class_info['methods']:
                    method_id = method['id']
                    cfg = cfg_graphs.get(method_id)
                    if cfg:
                        pdg = self._build_function_pdg(method, cfg)
                        self.graphs[method_id] = pdg
        
        print(f"✅ PDG built for {len(self.graphs)} functions")
        return self.graphs
    
    def _build_function_pdg(self, func_info: Dict, cfg: nx.DiGraph) -> nx.DiGraph:
        """Build PDG for a single function"""
        pdg = nx.DiGraph()
        
        # Add all CFG nodes as PDG nodes
        for node in cfg.nodes():
            pdg.add_node(node, **cfg.nodes[node])
        
        # Add control dependencies (from CFG)
        for u, v in cfg.edges():
            edge_type = cfg.edges[u, v].get('type')
            if edge_type in [EdgeType.CONDITIONAL_TRUE.value, 
                           EdgeType.CONDITIONAL_FALSE.value]:
                pdg.add_edge(u, v, type=EdgeType.CONTROL_DEPENDENCY.value)
        
        # Add data dependencies (simplified - analyze variable usage)
        variables = self._extract_variables(func_info)
        self._add_data_dependencies(pdg, cfg, variables)
        
        # Add function call dependencies
        for call in func_info.get('calls', []):
            # Find nodes that make this call
            for node in pdg.nodes():
                label = pdg.nodes[node].get('label', '')
                if call in label:
                    pdg.nodes[node]['calls'] = call
        
        return pdg
    
    def _extract_variables(self, func_info: Dict) -> Dict[str, List[int]]:
        """Extract variable definitions and uses"""
        variables = {}  # var_name -> [line_numbers where used]
        
        # Get parameters
        for param in func_info['parameters']:
            param_name = param['name']
            variables[param_name] = [func_info['start_line']]
        
        # Parse body for variable usage (simplified)
        body = func_info['body']
        for i, line in enumerate(body.split('\n')):
            # Simple pattern matching for assignments
            if '=' in line:
                parts = line.split('=')
                var_name = parts[0].strip().split()[-1]
                if var_name and var_name.isidentifier():
                    if var_name not in variables:
                        variables[var_name] = []
                    variables[var_name].append(func_info['start_line'] + i)
        
        return variables
    
    def _add_data_dependencies(self, pdg: nx.DiGraph, cfg: nx.DiGraph, 
                               variables: Dict[str, List[int]]):
        """Add data dependency edges"""
        # For each variable, connect its definition to its uses
        for var_name, lines in variables.items():
            if len(lines) < 2:
                continue
            
            def_line = lines[0]
            use_lines = lines[1:]
            
            # Find nodes at these lines
            def_nodes = [n for n in pdg.nodes() 
                        if pdg.nodes[n].get('line') == def_line]
            use_nodes = [n for n in pdg.nodes() 
                        if pdg.nodes[n].get('line') in use_lines]
            
            # Add edges from definition to uses
            for def_node in def_nodes:
                for use_node in use_nodes:
                    pdg.add_edge(
                        def_node, 
                        use_node,
                        type=EdgeType.DATA_DEPENDENCY.value,
                        variable=var_name
                    )
    
    def get_pdg(self, function_id: str) -> nx.DiGraph:
        """Get PDG for a specific function"""
        return self.graphs.get(function_id)
    
    def export_to_json(self, filename: str = "pdg.json"):
        """Export all PDGs to JSON"""
        data = {
            func_id: nx.node_link_data(pdg)
            for func_id, pdg in self.graphs.items()
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 PDG exported to {filename}")

# ============================================================================
# HYBRID GRAPH BUILDER
# ============================================================================

class HybridGraphBuilder:
    """Combines HPG, CFG, and PDG into a unified graph"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def build(self, hpg: nx.DiGraph, cfg_graphs: Dict[str, nx.DiGraph], 
              pdg_graphs: Dict[str, nx.DiGraph]) -> nx.DiGraph:
        """Build hybrid graph by merging HPG, CFG, and PDG"""
        print("🔨 Building Hybrid Graph (HPG + CFG + PDG)...")
        
        # Add all HPG nodes and edges
        self.graph.add_nodes_from(hpg.nodes(data=True))
        self.graph.add_edges_from(hpg.edges(data=True))
        
        # For each function, add its CFG and PDG
        for func_id, cfg in cfg_graphs.items():
            # Add CFG nodes with prefix
            for node, data in cfg.nodes(data=True):
                cfg_node_id = f"cfg_{node}"
                self.graph.add_node(cfg_node_id, graph_type="cfg", **data)
            
            # Add CFG edges
            for u, v, data in cfg.edges(data=True):
                self.graph.add_edge(f"cfg_{u}", f"cfg_{v}", graph_type="cfg", **data)
            
            # Link HPG function node to its CFG
            hpg_func_nodes = [n for n, d in self.graph.nodes(data=True) 
                             if 'function' in d.get('type', '') 
                             and func_id in n]
            if hpg_func_nodes:
                self.graph.add_edge(
                    hpg_func_nodes[0],
                    f"cfg_{func_id}_entry",
                    type="has_cfg"
                )
        
        # Add PDG information as edge attributes
        for func_id, pdg in pdg_graphs.items():
            for u, v, data in pdg.edges(data=True):
                edge_type = data.get('type')
                if edge_type == EdgeType.DATA_DEPENDENCY.value:
                    # Add data dependency info to corresponding CFG edges
                    cfg_u = f"cfg_{u}"
                    cfg_v = f"cfg_{v}"
                    if self.graph.has_edge(cfg_u, cfg_v):
                        self.graph.edges[cfg_u, cfg_v]['data_dep'] = data.get('variable')
        
        print(f"✅ Hybrid Graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        return self.graph
    
    def export_to_json(self, filename: str = "hybrid_graph.json"):
        """Export hybrid graph to JSON"""
        data = nx.node_link_data(self.graph)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 Hybrid Graph exported to {filename}")

# ============================================================================
# MAIN GRAPH NAVIGATOR
# ============================================================================

class GraphNavigator:
    """Main class to build and navigate all graphs"""
    
    def __init__(self, ir_file: str = "ir_output.json"):
        with open(ir_file, 'r') as f:
            self.ir_data = json.load(f)
        
        self.hpg_builder = HPGBuilder()
        self.cfg_builder = CFGBuilder()
        self.pdg_builder = PDGBuilder()
        self.hybrid_builder = HybridGraphBuilder()
        
        self.hpg = None
        self.cfg_graphs = None
        self.pdg_graphs = None
        self.hybrid_graph = None
    
    def build_all_graphs(self):
        """Build all graphs in order"""
        print("\n" + "="*60)
        print("🚀 BUILDING ALL GRAPHS")
        print("="*60 + "\n")
        
        # Build HPG (hierarchical structure)
        self.hpg = self.hpg_builder.build(self.ir_data)
        
        # Build CFG (control flow per function)
        self.cfg_graphs = self.cfg_builder.build(self.ir_data)
        
        # Build PDG (dependencies per function)
        self.pdg_graphs = self.pdg_builder.build(self.ir_data, self.cfg_graphs)
        
        # Build Hybrid Graph (combined)
        self.hybrid_graph = self.hybrid_builder.build(
            self.hpg,
            self.cfg_graphs,
            self.pdg_graphs
        )
        
        print("\n" + "="*60)
        print("✅ ALL GRAPHS BUILT SUCCESSFULLY")
        print("="*60 + "\n")
    
    def export_all(self, prefix: str = ""):
        """Export all graphs to JSON files"""
        self.hpg_builder.export_to_json(f"{prefix}hpg.json")
        self.cfg_builder.export_to_json(f"{prefix}cfg.json")
        self.pdg_builder.export_to_json(f"{prefix}pdg.json")
        self.hybrid_builder.export_to_json(f"{prefix}hybrid_graph.json")
    
    def get_function_context(self, function_name: str) -> Dict:
        """Get complete context for a function (for agents)"""
        context = {
            'function_name': function_name,
            'hierarchy': [],
            'cfg': None,
            'pdg': None,
            'dependencies': [],
            'complexity': 0
        }
        
        # Find function in HPG
        func_nodes = [
            (n, d) for n, d in self.hpg.nodes(data=True)
            if d.get('name') == function_name and 'function' in d.get('type', '')
        ]
        
        if not func_nodes:
            return context
        
        func_node, func_data = func_nodes[0]
        
        # Get hierarchy
        context['hierarchy'] = self.hpg_builder.get_hierarchy(func_node)
        context['complexity'] = func_data.get('complexity', 0)
        
        # Get CFG and PDG
        func_id = func_node.split('_', 1)[1]  # Extract ID from node name
        context['cfg'] = self.cfg_builder.get_cfg(func_id)
        context['pdg'] = self.pdg_builder.get_pdg(func_id)
        
        # Get dependencies (functions this calls)
        context['dependencies'] = func_data.get('calls', [])
        
        return context

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Initialize navigator
    navigator = GraphNavigator("ir_output.json")
    
    # Build all graphs
    navigator.build_all_graphs()
    
    # Export to files
    navigator.export_all()
    
    # Example: Get context for a specific function
    print("\n" + "="*60)
    print("📊 EXAMPLE: Getting Function Context")
    print("="*60 + "\n")
    
    # You can test with any function name from your code
    # context = navigator.get_function_context("your_function_name")
    # print(json.dumps(context, indent=2, default=str))

def visualize_graph(graph: nx.DiGraph, title="Graph"):
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(graph, seed=42)
    nx.draw_networkx_nodes(graph, pos, node_color='skyblue', node_size=800)
    nx.draw_networkx_edges(graph, pos, arrowstyle='->', arrowsize=20)
    labels = {n: graph.nodes[n].get('name', n) for n in graph.nodes()}
    nx.draw_networkx_labels(graph, pos, labels, font_size=10)
    plt.title(title)
    plt.axis('off')
    plt.show()

# Example: Build simple HPG
HPG = nx.DiGraph()
for file_ir in ir_data:
    # File node
    HPG.add_node(file_ir['file_name'], name=file_ir['file_name'])
    
    # Function nodes
    for func in file_ir.get('functions', []):
        HPG.add_node(func['id'], name=func['name'])
        HPG.add_edge(file_ir['file_name'], func['id'])
    
    # Class nodes
    for cls in file_ir.get('classes', []):
        HPG.add_node(cls['id'], name=cls['name'])
        HPG.add_edge(file_ir['file_name'], cls['id'])
        # Methods inside class
        for method in cls.get('methods', []):
            HPG.add_node(method['id'], name=method['name'])
            HPG.add_edge(cls['id'], method['id'])

visualize_graph(HPG, "Hierarchical Program Graph (HPG)")

# Example: Visualize CFG for first available function
CFG_example = nx.DiGraph()
# Pick first function with non-empty id
first_func = None
for file_ir in ir_data:
    if file_ir.get('functions'):
        for f in file_ir['functions']:
            if f['id'] != 'anonymous':
                first_func = f
                break
    if first_func:
        break

if first_func:
    # Dummy CFG edges (just for visualization)
    CFG_example.add_node(first_func['id'], name=first_func['name'])
    for i, call in enumerate(first_func.get('calls', [])):
        CFG_example.add_node(call, name=call)
        CFG_example.add_edge(first_func['id'], call)
    visualize_graph(CFG_example, f"CFG for {first_func['name']}")