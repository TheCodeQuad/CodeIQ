import json
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

class HPGGenerator:
    def __init__(self, ir_data):
        self.ir_data = ir_data
        self.graph = nx.DiGraph()
        
        # Color scheme for different node types
        self.colors = {
            'file': '#FF6B6B',
            'class': '#4ECDC4', 
            'function': '#45B7D1',
            'method': '#96CEB4',
            'variable': '#FFEAA7',
            'import': '#DDA0DD'
        }
        
        # Size scheme
        self.sizes = {
            'file': 3000,
            'class': 2000,
            'function': 1500,
            'method': 1200,
            'variable': 800,
            'import': 1000
        }

    def add_node_with_metadata(self, node_id, label, node_type, **attrs):
        """Add node with consistent styling"""
        self.graph.add_node(node_id, 
                           label=label, 
                           type=node_type,
                           color=self.colors[node_type],
                           size=self.sizes[node_type],
                           **attrs)

    def build_hpg(self):
        """Build the Hierarchical Program Graph"""
        print("🏗️ Building HPG...")
        
        # First pass: Add all nodes
        for file_ir in self.ir_data:
            self._add_file_nodes(file_ir)
        
        # Second pass: Add relationships
        for file_ir in self.ir_data:
            self._add_relationships(file_ir)
        
        print(f"✅ HPG built with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
        return self.graph

    def _add_file_nodes(self, file_ir):
        """Add file-level nodes"""
        file_id = f"file_{file_ir['file_name']}"
        self.add_node_with_metadata(
            file_id,
            f"📁 {file_ir['file_name']}\n({file_ir['language']})",
            'file',
            lines=file_ir['total_lines'],
            language=file_ir['language']
        )

        # Add imports
        for imp in file_ir.get('imports', []):
            import_id = f"import_{file_ir['file_name']}_{imp}"
            self.add_node_with_metadata(
                import_id,
                f"📦 {imp}",
                'import'
            )
            self.graph.add_edge(file_id, import_id, relationship="imports")

        # Add functions
        for func in file_ir['functions']:
            func_id = func['id']
            self.add_node_with_metadata(
                func_id,
                f"🔹 {func['name']}\n({len(func['parameters'])} params)",
                'function',
                params=len(func['parameters']),
                complexity=func['complexity'],
                lines=func['end_line'] - func['start_line'] + 1
            )
            self.graph.add_edge(file_id, func_id, relationship="contains")

        # Add classes and their methods
        for cls in file_ir['classes']:
            class_id = cls['id']
            self.add_node_with_metadata(
                class_id,
                f"🏛️ {cls['name']}\n{len(cls['methods'])} methods",
                'class',
                methods=len(cls['methods']),
                attributes=len(cls['attributes'])
            )
            self.graph.add_edge(file_id, class_id, relationship="contains")

            # Add methods
            for method in cls['methods']:
                method_id = method['id']
                self.add_node_with_metadata(
                    method_id,
                    f"🔸 {method['name']}\n({len(method['parameters'])} params)",
                    'method',
                    params=len(method['parameters']),
                    complexity=method['complexity']
                )
                self.graph.add_edge(class_id, method_id, relationship="contains")

        # Add variables
        for var in file_ir['variables']:
            var_id = f"var_{file_ir['file_name']}_{var['name']}"
            self.add_node_with_metadata(
                var_id,
                f"📝 {var['name']}",
                'variable'
            )
            self.graph.add_edge(file_id, var_id, relationship="contains")

    def _add_relationships(self, file_ir):
        """Add call relationships and dependencies"""
        
        # Function calls within the same file
        for func in file_ir['functions']:
            for call in func['calls']:
                # Try to find the called function in the same file
                for target_func in file_ir['functions']:
                    if target_func['name'] == call:
                        self.graph.add_edge(
                            func['id'], 
                            target_func['id'], 
                            relationship="calls"
                        )
                
                # Try to find in class methods
                for cls in file_ir['classes']:
                    for method in cls['methods']:
                        if method['name'] == call:
                            self.graph.add_edge(
                                func['id'],
                                method['id'],
                                relationship="calls"
                            )

        # Method calls within classes
        for cls in file_ir['classes']:
            for method in cls['methods']:
                for call in method['calls']:
                    # Check other methods in same class
                    for target_method in cls['methods']:
                        if target_method['name'] == call:
                            self.graph.add_edge(
                                method['id'],
                                target_method['id'],
                                relationship="calls"
                            )
                    
                    # Check functions in same file
                    for target_func in file_ir['functions']:
                        if target_func['name'] == call:
                            self.graph.add_edge(
                                method['id'],
                                target_func['id'],
                                relationship="calls"
                            )

    def visualize(self, output_file='hpg_visualization.png', layout='spring'):
        """Visualize the HPG"""
        print("🎨 Generating visualization...")
        
        plt.figure(figsize=(20, 15))
        
        # Choose layout
        if layout == 'spring':
            pos = nx.spring_layout(self.graph, k=3, iterations=50)
        elif layout == 'shell':
            pos = nx.shell_layout(self.graph)
        elif layout == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(self.graph)
        else:
            pos = nx.spring_layout(self.graph)
        
        # Prepare node colors and sizes
        node_colors = []
        node_sizes = []
        
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            node_colors.append(node_data['color'])
            node_sizes.append(node_data['size'])
        
        # Draw the graph
        nx.draw_networkx_nodes(self.graph, pos, 
                              node_color=node_colors,
                              node_size=node_sizes,
                              alpha=0.9)
        
        # Draw edges with different styles for different relationships
        edge_colors = []
        for u, v, data in self.graph.edges(data=True):
            rel = data.get('relationship', 'contains')
            if rel == 'calls':
                edge_colors.append('red')
            elif rel == 'imports':
                edge_colors.append('purple')
            else:  # contains
                edge_colors.append('gray')
        
        nx.draw_networkx_edges(self.graph, pos,
                              edge_color=edge_colors,
                              arrows=True,
                              arrowsize=20,
                              alpha=0.6)
        
        # Draw labels
        labels = {node: data['label'] for node, data in self.graph.nodes(data=True)}
        nx.draw_networkx_labels(self.graph, pos, labels, font_size=8)
        
        # Add legend
        self._add_legend()
        
        plt.title("Hierarchical Program Graph (HPG)", size=16)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"✅ Visualization saved as {output_file}")

    def _add_legend(self):
        """Add a legend to the plot"""
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=self.colors['file'], markersize=10, label='File'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=self.colors['class'], markersize=10, label='Class'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=self.colors['function'], markersize=10, label='Function'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=self.colors['method'], markersize=10, label='Method'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=self.colors['variable'], markersize=10, label='Variable'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=self.colors['import'], markersize=10, label='Import'),
            plt.Line2D([0], [0], color='gray', label='Contains'),
            plt.Line2D([0], [0], color='red', label='Calls'),
            plt.Line2D([0], [0], color='purple', label='Imports'),
        ]
        
        plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))

    def export_graphml(self, output_file='hpg_graph.graphml'):
        """Export graph to GraphML format for external tools"""
        nx.write_graphml(self.graph, output_file)
        print(f"✅ GraphML exported to {output_file}")

    def analyze_metrics(self):
        """Analyze graph metrics"""
        print("\n📊 HPG Metrics:")
        print(f"   Total nodes: {self.graph.number_of_nodes()}")
        print(f"   Total edges: {self.graph.number_of_edges()}")
        
        # Node type distribution
        node_types = [data['type'] for _, data in self.graph.nodes(data=True)]
        type_counts = defaultdict(int)
        for node_type in node_types:
            type_counts[node_type] += 1
        
        print("\n   Node Distribution:")
        for node_type, count in type_counts.items():
            print(f"     {node_type}: {count}")
        
        # Edge type distribution
        edge_types = [data.get('relationship', 'unknown') 
                     for _, _, data in self.graph.edges(data=True)]
        edge_counts = defaultdict(int)
        for edge_type in edge_types:
            edge_counts[edge_type] += 1
        
        print("\n   Edge Distribution:")
        for edge_type, count in edge_counts.items():
            print(f"     {edge_type}: {count}")
        
        # Graph density
        density = nx.density(self.graph)
        print(f"\n   Graph density: {density:.3f}")
        
        # Connected components
        components = list(nx.weakly_connected_components(self.graph))
        print(f"   Connected components: {len(components)}")

    def print_graph_summary(self):
        """Print a text summary of the graph"""
        print("\n📋 HPG Summary:")
        for file_ir in self.ir_data:
            print(f"\n📁 {file_ir['file_name']} ({file_ir['language']})")
            print(f"   Functions: {len(file_ir['functions'])}")
            print(f"   Classes: {len(file_ir['classes'])}")
            
            for func in file_ir['functions']:
                print(f"     🔹 {func['name']} (calls: {len(func['calls'])})")
            
            for cls in file_ir['classes']:
                print(f"     🏛️ {cls['name']}")
                for method in cls['methods']:
                    print(f"       🔸 {method['name']} (calls: {len(method['calls'])})")

# -------------------------------
# MAIN EXECUTION (Fixed)
# -------------------------------

def main():
    # Load your IR data
    try:
        with open('ir_output.json', 'r', encoding='utf-8') as f:
            ir_data = json.load(f)
    except FileNotFoundError:
        print("❌ IR file not found. Please run the IR generation first.")
        return
    
    print(f"📁 Loaded IR for {len(ir_data)} files")
    
    # Generate HPG
    hpg_generator = HPGGenerator(ir_data)
    graph = hpg_generator.build_hpg()
    
    # Print text summary first
    hpg_generator.print_graph_summary()
    
    # Analyze metrics
    hpg_generator.analyze_metrics()
    
    # Visualize (if graph is not too large)
    if graph.number_of_nodes() < 100:
        hpg_generator.visualize(output_file='hpg_visualization.png', layout='spring')
    else:
        print(f"⚠️  Graph has {graph.number_of_nodes()} nodes - too large for clear visualization")
        print("   Consider using the interactive version or GraphML export")
    
    # Export for external tools
    hpg_generator.export_graphml('hpg_graph.graphml')
    
    # Print some sample nodes and edges
    print("\n🔍 Sample Nodes:")
    for i, (node, data) in enumerate(list(graph.nodes(data=True))[:5]):
        print(f"   {node}: {data['label']}")
    
    print("\n🔍 Sample Edges:")
    for i, (u, v, data) in enumerate(list(graph.edges(data=True))[:5]):
        print(f"   {u} --[{data.get('relationship', 'unknown')}]--> {v}")

if __name__ == "__main__":
    main()