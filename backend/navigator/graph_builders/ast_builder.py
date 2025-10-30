# navigator/graph_builders/ast_builder.py
import os, json, sys
from pathlib import Path

# Add backend root to Python path so imports work from any directory
backend_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_root))

from navigator.visualizers.graph_visualizer import save_graph_html

def build_ast(ir_path):
    with open(ir_path, "r") as f:
        ir_data = json.load(f)

    ast_nodes = []
    ast_edges = []

    # Assuming IR has structure like: { "functions": [ { "name": ..., "body": [...] } ] }
    node_id = 0
    for func in ir_data.get("functions", []):
        func_id = node_id
        ast_nodes.append({"id": func_id, "label": f"Function: {func['name']}"})
        node_id += 1
        for stmt in func.get("body", []):
            stmt_id = node_id
            ast_nodes.append({"id": stmt_id, "label": stmt["type"]})
            ast_edges.append({"source": func_id, "target": stmt_id})
            node_id += 1

    graph_data = {"nodes": ast_nodes, "edges": ast_edges}
    
    # Use absolute path from backend root
    out_dir = backend_root / "data" / "graph_cache" / "ast"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / (Path(ir_path).stem + "_ast.html")

    save_graph_html(graph_data, out_path)
    print(f"🖼️  AST visualization saved at {out_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python ast_builder.py <path_to_ir.json>")
    else:
        build_ast(sys.argv[1])
