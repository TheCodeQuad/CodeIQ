import json
import networkx as nx
import matplotlib.pyplot as plt
import os
from collections import defaultdict

class PDGGenerator:
    def __init__(self):
        self.colors = {
            'entry': '#90EE90',      # Light green
            'exit': '#FFB6C1',       # Light red  
            'function': '#87CEEB',   # Light blue
            'method': '#96CEB4',     # Light green-blue
            'class': '#4ECDC4',      # Teal
            'file': '#FF6B6B',       # Light red
            'variable': '#FFEAA7',   # Light yellow
            'parameter': '#F0E68C',  # Khaki
            'condition': '#DDA0DD',  # Light purple
            'return': '#FFA07A',     # Light salmon
            'call': '#98FB98',       # Pale green
            'import': '#DDA0DD',     # Light purple
            'inheritance': '#FFD700', # Gold
            'metric': '#A9A9A9',     # Dark gray
            'unknown': '#CCCCCC'     # Light gray
        }
    
    def build_pdg_from_ir(self, ir_data):
        """Build PDG for entire codebase from IR data"""
        all_pdgs = {}
        
        print("🏗️ Building Program Dependence Graphs...")
        
        for file_ir in ir_data:
            filename = file_ir['file_name']
            print(f"\n📁 Processing {filename}")
            
            # Build PDG for this file
            file_pdg = self._build_file_pdg(file_ir)
            all_pdgs[filename] = file_pdg
            
            # Build PDGs for individual functions
            for func in file_ir['functions']:
                func_pdg = self._build_function_pdg(func, filename)
                all_pdgs[f"{filename}_{func['name']}"] = func_pdg
            
            # Build PDGs for classes and methods
            for cls in file_ir['classes']:
                class_pdg = self._build_class_pdg(cls, filename)
                all_pdgs[f"{filename}_{cls['name']}"] = class_pdg
                
                for method in cls['methods']:
                    method_pdg = self._build_function_pdg(method, filename, cls['name'])
                    all_pdgs[f"{filename}_{cls['name']}_{method['name']}"] = method_pdg
        
        print(f"✅ Built {len(all_pdgs)} PDGs")
        return all_pdgs
    
    def _build_file_pdg(self, file_ir):
        """Build PDG for entire file"""
        pdg = nx.DiGraph()
        
        # Add file node
        file_id = f"file_{file_ir['file_name'].replace('.', '_')}"
        pdg.add_node(file_id, 
                    label=f"📁 {file_ir['file_name']}\n({file_ir['language']})",
                    type='file',
                    language=file_ir['language'])
        
        # Add imports as data dependencies
        for imp in file_ir.get('imports', []):
            import_id = f"import_{imp.replace('.', '_')}"
            pdg.add_node(import_id, label=f"📦 {imp}", type='import')
            pdg.add_edge(import_id, file_id, type='data_dep', label='imports')
        
        # Add global variables
        for var in file_ir['variables']:
            var_id = f"var_{var['name']}"
            var_value = var.get('value', '?')
            if var_value and len(str(var_value)) > 20:
                var_value = str(var_value)[:17] + "..."
            pdg.add_node(var_id, 
                        label=f"📝 {var['name']}\n= {var_value}",
                        type='variable')
            pdg.add_edge(file_id, var_id, type='data_dep', label='declares')
        
        # Connect functions to file
        for func in file_ir['functions']:
            func_id = f"func_{func['name']}"
            pdg.add_node(func_id,
                        label=f"🔹 {func['name']}\n({len(func['parameters'])} params)",
                        type='function')
            pdg.add_edge(file_id, func_id, type='data_dep', label='contains')
            
            # Add function dependencies
            self._add_function_dependencies(pdg, func, func_id)
        
        # Connect classes to file
        for cls in file_ir['classes']:
            class_id = f"class_{cls['name']}"
            pdg.add_node(class_id,
                        label=f"🏛️ {cls['name']}\n{len(cls['methods'])} methods",
                        type='class')
            pdg.add_edge(file_id, class_id, type='data_dep', label='contains')
            
            # Add class dependencies
            self._add_class_dependencies(pdg, cls, class_id)
        
        return pdg
    
    def _build_function_pdg(self, func, filename, class_name=None):
        """Build PDG for a single function/method"""
        pdg = nx.DiGraph()
        
        # Function identifier
        if class_name:
            func_id = f"method_{class_name}_{func['name']}"
            func_label = f"🔸 {class_name}.{func['name']}"
            node_type = 'method'
        else:
            func_id = f"func_{func['name']}"
            func_label = f"🔹 {func['name']}"
            node_type = 'function'
        
        # Add function node
        pdg.add_node('entry', label='ENTRY', type='entry')
        pdg.add_node(func_id, label=func_label, type=node_type)
        pdg.add_node('exit', label='EXIT', type='exit')
        
        pdg.add_edge('entry', func_id, type='control_dep', label='calls')
        pdg.add_edge(func_id, 'exit', type='control_dep', label='returns')
        
        # Add parameters as data dependencies
        for param in func['parameters']:
            param_id = f"param_{param['name']}"
            param_label = f"📌 {param['name']}"
            if param.get('type'):
                param_label += f"\n: {param['type']}"
            if param.get('default'):
                default_val = param['default']
                if len(str(default_val)) > 15:
                    default_val = str(default_val)[:12] + "..."
                param_label += f"\n= {default_val}"
            
            pdg.add_node(param_id, label=param_label, type='parameter')
            pdg.add_edge(func_id, param_id, type='data_dep', label='uses')
        
        # Add return type dependency
        if func.get('return_type'):
            return_id = f"return_{func['name']}"
            pdg.add_node(return_id, label=f"🔄 returns {func['return_type']}", type='return')
            pdg.add_edge(func_id, return_id, type='data_dep', label='returns')
        
        # Add function calls as dependencies
        for call in func.get('calls', []):
            call_id = f"call_{call}"
            pdg.add_node(call_id, label=f"📞 calls {call}", type='call')
            pdg.add_edge(func_id, call_id, type='control_dep', label='calls')
        
        # Add complexity as metric
        if func.get('complexity'):
            complexity_id = f"complexity_{func['name']}"
            pdg.add_node(complexity_id, label=f"📊 complexity: {func['complexity']}", type='metric')
            pdg.add_edge(func_id, complexity_id, type='data_dep', label='measures')
        
        return pdg
    
    def _build_class_pdg(self, cls, filename):
        """Build PDG for a class"""
        pdg = nx.DiGraph()
        
        class_id = f"class_{cls['name']}"
        pdg.add_node(class_id, 
                    label=f"🏛️ {cls['name']}",
                    type='class')
        
        # Add inheritance dependency
        if cls.get('superclass'):
            super_id = f"super_{cls['superclass']}"
            pdg.add_node(super_id, label=f"📚 extends {cls['superclass']}", type='inheritance')
            pdg.add_edge(super_id, class_id, type='data_dep', label='extends')
        
        # Add methods
        for method in cls.get('methods', []):
            method_id = f"method_{cls['name']}_{method['name']}"
            pdg.add_node(method_id,
                        label=f"🔸 {method['name']}\n({len(method.get('parameters', []))} params)",
                        type='method')
            pdg.add_edge(class_id, method_id, type='data_dep', label='contains')
        
        # Add attributes
        for attr in cls.get('attributes', []):
            attr_id = f"attr_{cls['name']}_{attr}"
            pdg.add_node(attr_id, label=f"📝 {attr}", type='variable')
            pdg.add_edge(class_id, attr_id, type='data_dep', label='has')
        
        return pdg
    
    def _add_function_dependencies(self, pdg, func, func_id):
        """Add dependencies for a function"""
        # Add parameter dependencies
        for param in func.get('parameters', []):
            param_id = f"param_{func['name']}_{param['name']}"
            pdg.add_node(param_id, label=f"📌 {param['name']}", type='parameter')
            pdg.add_edge(func_id, param_id, type='data_dep', label='uses')
        
        # Add call dependencies
        for call in func.get('calls', []):
            call_id = f"call_{func['name']}_{call}"
            pdg.add_node(call_id, label=f"📞 {call}", type='call')
            pdg.add_edge(func_id, call_id, type='control_dep', label='calls')
    
    def _add_class_dependencies(self, pdg, cls, class_id):
        """Add dependencies for a class"""
        # Method dependencies
        for method in cls.get('methods', []):
            method_id = f"method_{cls['name']}_{method['name']}"
            pdg.add_node(method_id, label=f"🔸 {method['name']}", type='method')
            pdg.add_edge(class_id, method_id, type='data_dep', label='has')
            
            # Method calls
            for call in method.get('calls', []):
                call_id = f"call_{cls['name']}_{method['name']}_{call}"
                pdg.add_node(call_id, label=f"📞 {call}", type='call')
                pdg.add_edge(method_id, call_id, type='control_dep', label='calls')
    
    def visualize_pdg(self, pdg, title, output_file=None):
        """Visualize a single PDG"""
        if pdg.number_of_nodes() == 0:
            print(f"    ⚠️  Empty PDG for {title}, skipping visualization")
            return
        
        plt.figure(figsize=(15, 10))
        
        # Use spring layout for better PDG visualization
        pos = nx.spring_layout(pdg, k=1, iterations=50)
        
        # Color nodes by type
        node_colors = []
        node_sizes = []
        for node in pdg.nodes():
            node_type = pdg.nodes[node].get('type', 'unknown')
            node_colors.append(self.colors.get(node_type, '#CCCCCC'))
            
            # Adjust sizes based on node type
            size_map = {
                'entry': 1200, 'exit': 1200,
                'function': 2000, 'method': 1800,
                'class': 2500, 'file': 3000,
                'variable': 1500, 'call': 1400,
                'parameter': 1300, 'import': 1400,
                'return': 1400, 'inheritance': 1600,
                'metric': 1200, 'unknown': 1000
            }
            node_sizes.append(size_map.get(node_type, 1200))
        
        # Draw nodes
        nx.draw_networkx_nodes(pdg, pos, 
                              node_color=node_colors,
                              node_size=node_sizes,
                              alpha=0.9,
                              edgecolors='black',
                              linewidths=1)
        
        # Draw edges with different styles for dependency types
        edge_colors = []
        edge_styles = []
        edge_widths = []
        
        for u, v, data in pdg.edges(data=True):
            edge_type = data.get('type', 'unknown')
            if edge_type == 'control_dep':
                edge_colors.append('red')
                edge_styles.append('solid')
                edge_widths.append(2)
            elif edge_type == 'data_dep':
                edge_colors.append('blue')
                edge_styles.append('dashed')
                edge_widths.append(1.5)
            else:
                edge_colors.append('gray')
                edge_styles.append('dotted')
                edge_widths.append(1)
        
        # Draw edges
        for (u, v, data), color, style, width in zip(pdg.edges(data=True), edge_colors, edge_styles, edge_widths):
            nx.draw_networkx_edges(pdg, pos, 
                                  edgelist=[(u, v)],
                                  edge_color=color,
                                  style=style,
                                  width=width,
                                  arrows=True,
                                  arrowsize=15,
                                  alpha=0.7)
        
        # Draw labels
        labels = {node: pdg.nodes[node].get('label', node) for node in pdg.nodes()}
        nx.draw_networkx_labels(pdg, pos, labels, font_size=7)
        
        # Add legend
        self._add_pdg_legend()
        
        plt.title(f"Program Dependence Graph: {title}", size=14)
        plt.axis('off')
        plt.tight_layout()
        
        if output_file:
            try:
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                print(f"    ✅ PDG saved as {output_file}")
            except Exception as e:
                print(f"    ❌ Error saving {output_file}: {e}")
        
        plt.show()
    
    def _add_pdg_legend(self):
        """Add legend for PDG"""
        legend_elements = [
            # Node types
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=self.colors['file'], markersize=8, label='File'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=self.colors['class'], markersize=8, label='Class'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=self.colors['function'], markersize=8, label='Function'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=self.colors['method'], markersize=8, label='Method'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=self.colors['variable'], markersize=8, label='Variable'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=self.colors['parameter'], markersize=8, label='Parameter'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=self.colors['call'], markersize=8, label='Function Call'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=self.colors['import'], markersize=8, label='Import'),
            
            # Edge types
            plt.Line2D([0], [0], color='red', linestyle='solid', linewidth=2, label='Control Dependency'),
            plt.Line2D([0], [0], color='blue', linestyle='dashed', linewidth=1.5, label='Data Dependency'),
            plt.Line2D([0], [0], color='gray', linestyle='dotted', linewidth=1, label='Other Dependency'),
        ]
        
        plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1), fontsize=8)

    def analyze_pdg_metrics(self, all_pdgs):
        """Analyze PDG metrics"""
        print("\n📊 PDG Metrics Analysis:")
        
        total_nodes = 0
        total_edges = 0
        dependency_types = defaultdict(int)
        node_types = defaultdict(int)
        
        for name, pdg in all_pdgs.items():
            total_nodes += pdg.number_of_nodes()
            total_edges += pdg.number_of_edges()
            
            # Count node types
            for node in pdg.nodes():
                node_type = pdg.nodes[node].get('type', 'unknown')
                node_types[node_type] += 1
            
            # Count edge types
            for u, v, data in pdg.edges(data=True):
                dep_type = data.get('type', 'unknown')
                dependency_types[dep_type] += 1
        
        print(f"   Total PDGs: {len(all_pdgs)}")
        print(f"   Total nodes: {total_nodes}")
        print(f"   Total edges: {total_edges}")
        
        print(f"\n   Node Types:")
        for node_type, count in sorted(node_types.items()):
            print(f"     {node_type}: {count}")
        
        print(f"\n   Dependency Types:")
        for dep_type, count in sorted(dependency_types.items()):
            print(f"     {dep_type}: {count}")

# -------------------------------
# MAIN EXECUTION
# -------------------------------

def generate_pdgs_from_ir(ir_file='ir_output.json', output_dir='pdgs'):
    """Generate PDGs for entire codebase from IR"""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Load IR data
    try:
        with open(ir_file, 'r', encoding='utf-8') as f:
            ir_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ IR file not found: {ir_file}")
        return {}
    
    print(f"📁 Loaded IR for {len(ir_data)} files")
    
    # Generate PDGs
    pdg_generator = PDGGenerator()
    all_pdgs = pdg_generator.build_pdg_from_ir(ir_data)
    
    # Visualize PDGs (limit to first few to avoid too many images)
    print("\n🎨 Generating PDG visualizations...")
    visualized_count = 0
    max_visualizations = 100  # Limit to avoid too many images
    
    for name, pdg in all_pdgs.items():
        if visualized_count >= max_visualizations:
            print(f"    ⚠️  Limited to first {max_visualizations} visualizations")
            break
            
        if pdg.number_of_nodes() > 1:  # Only visualize non-empty graphs
            output_file = os.path.join(output_dir, f"pdg_{name.replace('/', '_').replace('.', '_')}.png")
            pdg_generator.visualize_pdg(pdg, name, output_file)
            visualized_count += 1
    
    # Analyze metrics
    pdg_generator.analyze_pdg_metrics(all_pdgs)
    
    # Export GraphML for external tools
    print("\n💾 Exporting GraphML files...")
    exported_count = 0
    for name, pdg in all_pdgs.items():
        if pdg.number_of_nodes() > 0:
            graphml_file = os.path.join(output_dir, f"pdg_{name.replace('/', '_').replace('.', '_')}.graphml")
            try:
                nx.write_graphml(pdg, graphml_file)
                exported_count += 1
            except Exception as e:
                print(f"    ❌ Error exporting {graphml_file}: {e}")
    
    print(f"✅ Exported {exported_count} GraphML files")
    print(f"\n🎉 Completed! Generated {len(all_pdgs)} PDGs")
    
    # Print sample dependencies from first few PDGs
    print("\n🔍 Sample Dependencies:")
    sample_count = 0
    for name, pdg in all_pdgs.items():
        if sample_count >= 3:
            break
        if pdg.number_of_edges() > 0:
            print(f"\n  {name}:")
            edges = list(pdg.edges(data=True))[:3]
            for u, v, data in edges:
                dep_type = data.get('type', 'unknown')
                u_label = pdg.nodes[u].get('label', u)
                v_label = pdg.nodes[v].get('label', v)
                print(f"    {u_label} --[{dep_type}]--> {v_label}")
            sample_count += 1
    
    return all_pdgs

if __name__ == "__main__":
    print("🎯 Program Dependence Graph Generation Started")
    all_pdgs = generate_pdgs_from_ir()
    print(f"\n🎉 Completed! Generated {len(all_pdgs)} PDGs")