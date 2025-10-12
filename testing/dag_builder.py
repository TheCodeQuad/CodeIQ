# dag_generator.py
import os
import json
from collections import defaultdict
from tree_sitter import Language, Parser
import networkx as nx

# ---- CONFIG ----
PROJECT_ROOT = os.path.dirname(__file__)              # parser/
LIB_PATH = os.path.join(PROJECT_ROOT, "build", "my-languages.so")
SOURCE_ROOT = os.path.normpath(os.path.join(PROJECT_ROOT, "..", "source_files/flask_app"))

# Supported extensions -> tree-sitter language name
EXT_TO_LANG = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".c": "c",
    ".ts": "typescript"
}

# Node types for definitions and calls per language (heuristic set)
FUNC_NODE_TYPES = {
    "python": ("function_definition",),
    "java": ("method_declaration", "function_declaration"),
    "javascript": ("function_declaration", "method_definition"),
    "c": ("function_definition",),
    "typescript": ("function_declaration", "method_definition"),
}

CLASS_NODE_TYPES = {
    "python": ("class_definition",),
    "java": ("class_declaration",),
    "javascript": ("class_declaration",),
    "c": tuple(),   # C doesn't have class defs in this sense
    "typescript": ("class_declaration",),
}

CALL_NODE_TYPES = {
    "python": ("call",),
    "java": ("method_invocation", "call_expression"),
    "javascript": ("call_expression",),
    "c": ("call_expression",),
    "typescript": ("call_expression",),
}

# ---- helpers ----
def load_languages(lib_path):
    langs = {}
    for ext, lang_name in EXT_TO_LANG.items():
        try:
            langs[ext] = Language(lib_path, lang_name)
        except Exception as e:
            print(f"ERROR loading language {lang_name} from {lib_path}: {e}")
            raise
    return langs

def read_file_bytes(path):
    with open(path, "rb") as f:
        return f.read()

def get_text(node, code_bytes):
    return code_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")

def find_first_identifier_descendant(node, code_bytes):
    # Depth-first search for identifier-like tokens
    stack = [node]
    while stack:
        n = stack.pop()
        if n.type in ("identifier", "property_identifier", "scoped_identifier", "name"):
            return get_text(n, code_bytes)
        stack.extend(reversed(n.children))
    return None

# Find definitions (functions and classes) with ranges
def collect_definitions(file_path, parser, code_bytes, lang_name):
    root = parser.parse(code_bytes).root_node
    funcs = []
    classes = []

    def walk(node):
        # function nodes
        if node.type in FUNC_NODE_TYPES.get(lang_name, ()):
            name = find_first_identifier_descendant(node, code_bytes) or "<anon>"
            funcs.append({
                "name": name,
                "start": node.start_point[0] + 1,
                "end": node.end_point[0] + 1,
                "node": node
            })
        if node.type in CLASS_NODE_TYPES.get(lang_name, ()):
            name = find_first_identifier_descendant(node, code_bytes) or "<anon>"
            classes.append({
                "name": name,
                "start": node.start_point[0] + 1,
                "end": node.end_point[0] + 1,
                "node": node
            })
        for c in node.children:
            walk(c)

    walk(root)
    return funcs, classes

# Find calls inside a node (function body)
def collect_calls_in_node(node, code_bytes, lang_name):
    calls = []

    def walk(n):
        if n.type in CALL_NODE_TYPES.get(lang_name, ()):
            # try to extract the called identifier
            called = find_first_identifier_descendant(n, code_bytes)
            if called:
                calls.append(called)
        for c in n.children:
            walk(c)
    walk(node)
    return calls

# map module name (python) to file path if exists in project
def module_name_to_path(module_name):
    # e.g. pkg.sub -> pkg/sub.py or pkg/sub/__init__.py
    rel = module_name.replace(".", os.sep)
    candidates = [
        os.path.join(SOURCE_ROOT, rel + ".py"),
        os.path.join(SOURCE_ROOT, rel, "__init__.py"),
    ]
    for cand in candidates:
        if os.path.exists(cand):
            return os.path.normpath(cand)
    return None

# Recursively collect all source files we care about
def collect_source_files(root):
    files = []
    for dirpath, _, filenames in os.walk(root):
        # ignore venvs
        if "venv" in dirpath.split(os.sep):
            continue
        for fn in filenames:
            ext = os.path.splitext(fn)[1]
            if ext in EXT_TO_LANG:
                files.append(os.path.join(dirpath, fn))
    return files

# ---- main DAG building ----
def build_dependency_graph():
    langs = load_languages(LIB_PATH)
    G = nx.DiGraph()

    # global maps
    func_index = defaultdict(list)   # name -> list of (id, file_path, start, end)
    file_nodes = set()

    parser = Parser()

    source_files = collect_source_files(SOURCE_ROOT)
    print(f"Found {len(source_files)} source files.")

    file_defs = {}  # file -> {functions:[], classes:[], imports:[]}

    # First pass: collect defs and imports
    for fp in source_files:
        ext = os.path.splitext(fp)[1]
        lang = EXT_TO_LANG.get(ext)
        parser.set_language(langs[ext])
        code_bytes = read_file_bytes(fp)
        funcs, classes = collect_definitions(fp, parser, code_bytes, lang)
        file_key = os.path.relpath(fp, SOURCE_ROOT)
        file_nodes.add(file_key)
        file_defs[file_key] = {"functions": funcs, "classes": classes, "imports": []}

        # index functions by name (for simple name matching)
        for f in funcs:
            fid = f"FUNC::{file_key}::{f['name']}::{f['start']}"
            func_index[f['name']].append({
                "id": fid, "file": file_key, "start": f["start"], "end": f["end"]
            })
            G.add_node(fid, type="function", file=file_key, name=f["name"])
        for c in classes:
            cid = f"CLASS::{file_key}::{c['name']}"
            G.add_node(cid, type="class", file=file_key, name=c["name"])

        # Collect simple imports (python)
        if lang == "python":
            root = parser.parse(code_bytes).root_node
            for child in root.children:
                if child.type in ("import_statement", "import_from_statement"):
                    txt = get_text(child, code_bytes).strip()
                    # try to parse module name heuristically
                    # for "from a.b import c" we want "a.b"
                    parts = txt.split()
                    mod = None
                    if parts[0] == "import" and len(parts) >= 2:
                        mod = parts[1].split(",")[0]
                    elif parts[0] == "from" and len(parts) >= 2:
                        mod = parts[1]
                    if mod:
                        mapped = module_name_to_path(mod)
                        if mapped:
                            mapped_key = os.path.relpath(mapped, SOURCE_ROOT)
                            file_defs[file_key]["imports"].append(mapped_key)
                            G.add_node(f"FILE::{mapped_key}", type="file")
                            G.add_node(f"FILE::{file_key}", type="file")
                            G.add_edge(f"FILE::{file_key}", f"FILE::{mapped_key}", type="import")
    # End first pass

    # Second pass: collect calls and resolve to functions
    for fp in source_files:
        ext = os.path.splitext(fp)[1]
        lang = EXT_TO_LANG.get(ext)
        parser.set_language(langs[ext])
        code_bytes = read_file_bytes(fp)
        root = parser.parse(code_bytes).root_node
        file_key = os.path.relpath(fp, SOURCE_ROOT)

        # for each function node, collect calls inside and add edges
        for f in file_defs[file_key]["functions"]:
            # find the exact node for this function:
            fnode = f["node"]
            calls = collect_calls_in_node(fnode, code_bytes, lang)
            src_id = f"FUNC::{file_key}::{f['name']}::{f['start']}"
            for called_name in calls:
                # attempt resolution:
                targets = func_index.get(called_name, [])
                if targets:
                    # prefer same-file targets if any
                    same_file_targets = [t for t in targets if t["file"] == file_key]
                    chosen = same_file_targets if same_file_targets else targets
                    for t in chosen:
                        G.add_edge(src_id, t["id"], type="call")
                else:
                    # unknown target: add a placeholder node
                    unknown_id = f"UNK::{called_name}"
                    if not G.has_node(unknown_id):
                        G.add_node(unknown_id, type="unknown", name=called_name)
                    G.add_edge(src_id, unknown_id, type="call")

    # Optional: add class inheritance edges (heuristic: check class nodes text for parent name)
    # Simple heuristic: scan class node text for "(" then identifier inside
    for file_key, info in file_defs.items():
        for c in info["classes"]:
            node = c["node"]
            code_bytes = read_file_bytes(os.path.join(SOURCE_ROOT, file_key))
            text = get_text(node, code_bytes)
            # find pattern like class Name(Base):
            import re
            m = re.search(r"class\s+\w+\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)", text)
            if m:
                base = m.group(1)
                # try to resolve base in indexed classes
                # find class nodes by name across files
                for fk2, info2 in file_defs.items():
                    for c2 in info2["classes"]:
                        if c2["name"] == base:
                            cid_child = f"CLASS::{file_key}::{c['name']}"
                            cid_parent = f"CLASS::{fk2}::{c2['name']}"
                            G.add_edge(cid_child, cid_parent, type="inherits")

    # Save graph to JSON (nodes and edges)
    nodes_out = []
    for n, data in G.nodes(data=True):
        nodes_out.append({"id": n, **data})
    edges_out = []
    for u, v, data in G.edges(data=True):
        edges_out.append({"src": u, "dst": v, **data})

    out = {"nodes": nodes_out, "edges": edges_out}
    out_path = os.path.join(PROJECT_ROOT, "dag.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(f"Wrote DAG to {out_path}")
    print("Graph stats: nodes =", G.number_of_nodes(), "edges =", G.number_of_edges())
    print("Is DAG?", nx.is_directed_acyclic_graph(G))
    if nx.is_directed_acyclic_graph(G):
        topo = list(nx.topological_sort(G))
        print("Topological order (partial):", topo[:40])

    # Optional visualization (requires matplotlib)
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(12, 9))
        pos = nx.spring_layout(G, k=0.5)
        # draw function nodes and unknowns
        node_colors = []
        for n, data in G.nodes(data=True):
            t = data.get("type", "other")
            if t == "function":
                node_colors.append("lightblue")
            elif t == "file":
                node_colors.append("lightgreen")
            elif t == "class":
                node_colors.append("orange")
            else:
                node_colors.append("lightgrey")
        nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=1200, font_size=8, arrowsize=12)
        plt.title("Dependency Graph")
        plt.show()
    except Exception:
        print("matplotlib not available or drawing failed; dag.json saved.")
    return G

if __name__ == "__main__":
    build_dependency_graph()
