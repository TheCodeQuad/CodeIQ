# navigator/graph_builders/cfg_builder.py
import os
import json
import sys
from collections import defaultdict
from pathlib import Path
from pyvis.network import Network
import networkx as nx

# Add backend root to Python path so imports work from any directory
backend_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_root))

class CFGNode:
    def __init__(self, id, label, file_path, line_no):
        self.id = id
        self.label = label
        self.file_path = file_path
        self.line_no = line_no
        self.next_nodes = []

    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "file_path": self.file_path,
            "line_no": self.line_no,
            "next_nodes": self.next_nodes
        }


class CFGBuilder:
    """Builds Control Flow Graph (CFG) from parsed IR data."""
    def __init__(self, ir_data):
        self.ir_data = ir_data
        self.graph = defaultdict(list)
        self.nodes = {}

    def build(self):
        node_id = 0

        for file_info in self.ir_data.get("files", []):
            file_path = file_info["path"]
            for func in file_info.get("functions", []):
                prev_node_id = None

                for call in func.get("calls", []):
                    node = CFGNode(
                        id=node_id,
                        label=f"{func['name']} → {call}",
                        file_path=file_path,
                        line_no=func["start_line"]
                    )
                    self.nodes[node_id] = node

                    if prev_node_id is not None:
                        self.graph[prev_node_id].append(node_id)

                    prev_node_id = node_id
                    node_id += 1

                if prev_node_id is not None:
                    self.graph[prev_node_id].append(f"exit_{func['name']}")

        return self._serialize()

    def _serialize(self):
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [
                {"from": src, "to": dst}
                for src, dst_list in self.graph.items()
                for dst in dst_list
            ],
            "summary": {
                "total_nodes": len(self.nodes),
                "total_edges": sum(len(v) for v in self.graph.values())
            }
        }


def visualize_cfg(cfg, output_html):
    """Create an interactive HTML visualization of the CFG."""
    net = Network(height="800px", width="100%", directed=True, bgcolor="#222222", font_color="white")

    G = nx.DiGraph()
    for edge in cfg["edges"]:
        G.add_edge(edge["from"], edge["to"])

    for node in cfg["nodes"]:
        label = node["label"]
        title = f"<b>{node['file_path']}</b><br>Line: {node['line_no']}"
        net.add_node(node["id"], label=label, title=title)

    # layout – hierarchical top-down
    net.set_options("""
    var options = {
      "layout": {"hierarchical": {"direction": "UD", "sortMethod": "directed"}},
      "edges": {"color": {"color": "#AAAAAA"}, "arrows": {"to": {"enabled": true}}},
      "nodes": {"color": {"background": "#29b6f6", "border": "#0288d1"}}
    }
    """)
    net.from_nx(G)
    net.save_graph(output_html)
    print(f"🌐 HTML visualization saved at {output_html}")


def save_cfg(ir_path, output_dir="data/graph_cache/cfg"):
    """Builds and saves a Control Flow Graph for the given IR file."""
    os.makedirs(output_dir, exist_ok=True)
    with open(ir_path, "r", encoding="utf-8") as f:
        ir_data = json.load(f)

    builder = CFGBuilder(ir_data)
    cfg = builder.build()

    repo_name = Path(ir_path).stem
    json_path = os.path.join(output_dir, f"{repo_name}_cfg.json")
    html_path = os.path.join(output_dir, f"{repo_name}_cfg.html")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    visualize_cfg(cfg, html_path)

    print(f"✅ CFG built and saved at {json_path}")
    return cfg


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        save_cfg(sys.argv[1])
    else:
        print("Usage: python cfg_builder.py <path_to_ir.json>")
