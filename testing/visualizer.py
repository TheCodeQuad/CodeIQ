# visualize_graphs.py
import networkx as nx
import matplotlib.pyplot as plt

def visualize_graph(graph_path, title):
    G = nx.read_gexf(graph_path)
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42)
    nx.draw(G, pos, with_labels=True, node_size=1000, node_color="lightblue", font_size=8, font_weight="bold", edge_color="gray")
    plt.title(title)
    plt.show()

if __name__ == "__main__":
    visualize_graph("cfg_graph.gexf", "Control Flow Graph (CFG)")
    visualize_graph("pdg_graph.gexf", "Program Dependency Graph (PDG)")
    visualize_graph("hpg_graph.gexf", "Hybrid Program Graph (HPG)")
