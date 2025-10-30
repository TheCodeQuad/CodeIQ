"""
Robust graph generators (HPG, CFG, PDG) from the IR saved in parser/output/ir_output.json.

This script:
 - Loads the IR JSON (expected shape: each file -> IRNode.to_dict() as produced by ir_builder)
 - Traverses the IR to locate function and class nodes
 - Generates:
    - HPG (one graph for entire repo)
    - CFG (one graph per function with at least 1 statement)
    - PDG (one graph per function if there are variable defs/uses)
 - Skips empty graphs to avoid blank PNGs
 - Prints diagnostics for each file/function processed
"""

import os
import json
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, Any, List

# Paths
BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
GRAPH_DIR = os.path.join(OUTPUT_DIR, "graphs")
CFG_DIR = os.path.join(GRAPH_DIR, "cfg")
PDG_DIR = os.path.join(GRAPH_DIR, "pdg")

os.makedirs(CFG_DIR, exist_ok=True)
os.makedirs(PDG_DIR, exist_ok=True)
os.makedirs(GRAPH_DIR, exist_ok=True)

IR_PATH = os.path.join(OUTPUT_DIR, "ir_output.json")

# ---------- Utility helpers ----------

def load_ir() -> Dict[str, Any]:
    if not os.path.exists(IR_PATH):
        raise FileNotFoundError(f"IR file not found at {IR_PATH}")
    with open(IR_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def safe_label(s: str, max_len: int = 40) -> str:
    if s is None:
        return ""
    s = str(s).strip().replace("\n", " ")
    return (s[:max_len] + "...") if len(s) > max_len else s

def find_functions_in_ir(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Given an IR node (dict), recursively find function-like nodes.
    We treat nodes with node['type'] == 'function' or containing 'function' in type.
    """
    found = []
    node_type = node.get("type", "").lower()
    if node_type == "function" or "function" in node_type or "method" in node_type:
        found.append(node)
    # Some IRs might store functions under children even if type is 'module' or 'file'
    for child in node.get("children", []) or []:
        found.extend(find_functions_in_ir(child))
    return found

def find_classes_in_ir(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    found = []
    node_type = node.get("type", "").lower()
    if "class" in node_type:
        found.append(node)
    for child in node.get("children", []) or []:
        found.extend(find_classes_in_ir(child))
    return found

def extract_statements_from_function(func_node: Dict[str, Any]) -> List[str]:
    """
    Heuristic: function children (assignments, return, if, call) become 'statements'.
    We will flatten immediate children into string labels.
    """
    stmts = []
    for c in func_node.get("children", []) or []:
        # use available representative fields
        typ = c.get("type", "")
        name = c.get("name")
        lhs = c.get("lhs")
        rhs = c.get("rhs")
        # if it's an assignment/return/expr, summarize
        if typ:
            if name:
                label = f"{typ}: {name}"
            elif lhs or rhs:
                label = f"{typ}: {lhs if lhs else ''} = {rhs if rhs else ''}"
            else:
                # try get nested textual representation
                label = typ
        else:
            label = str(c)[:60]
        stmts.append(safe_label(label))
    return stmts

def extract_var_defs_and_uses(func_node: Dict[str, Any]):
    """
    Use 'defines' and 'uses' lists if present. Fallback: search children for defines/uses.
    """
    defines = []
    uses = []
    if "defines" in func_node:
        defines = func_node.get("defines") or []
    if "uses" in func_node:
        uses = func_node.get("uses") or []

    # Walk children for nested defines/uses
    for c in func_node.get("children", []) or []:
        if isinstance(c, dict):
            if "defines" in c:
                defines.extend(c.get("defines") or [])
            if "uses" in c:
                uses.extend(c.get("uses") or [])
    # make unique and string
    defines = list(dict.fromkeys([str(x) for x in defines if x]))
    uses = list(dict.fromkeys([str(x) for x in uses if x]))
    return defines, uses

# ---------- HPG (Hierarchical Program Graph) ----------

def generate_hpg(ir_data: Dict[str, Any]):
    print("Generating HPG...")
    G = nx.DiGraph()

    for file_path, file_ir in ir_data.items():
        basename = os.path.basename(file_path)
        file_node = f"FILE::{basename}"
        G.add_node(file_node, kind="file")
        # add classes
        classes = find_classes_in_ir(file_ir) if isinstance(file_ir, dict) else []
        for cls in classes:
            cls_name = cls.get("name") or f"class@{cls.get('start', '')}"
            cls_node = f"CLASS::{basename}::{cls_name}"
            G.add_node(cls_node, kind="class")
            G.add_edge(file_node, cls_node)
            # attach methods
            methods = find_functions_in_ir(cls)
            for m in methods:
                mname = m.get("name") or f"method@{m.get('start','')}"
                mnode = f"FUNC::{basename}::{mname}"
                G.add_node(mnode, kind="function")
                G.add_edge(cls_node, mnode)

        # add file-level functions
        funcs = find_functions_in_ir(file_ir) if isinstance(file_ir, dict) else []
        for fnode in funcs:
            # skip methods already attached to class (they will appear inside class children)
            parent_type = fnode.get("_parent_type_marker")
            name = fnode.get("name") or f"func@{fnode.get('start','')}"
            node_id = f"FUNC::{basename}::{name}"
            # avoid duplicate nodes
            if not G.has_node(node_id):
                G.add_node(node_id, kind="function")
                G.add_edge(file_node, node_id)

    # if graph empty, exit
    if G.number_of_nodes() == 0:
        print("HPG: No nodes found in IR — skipping HPG generation.")
        return None

    plt.figure(figsize=(12, 9))
    pos = nx.spring_layout(G, k=0.5, iterations=100)
    node_colors = ["#9ecae1" if d.get("kind")=="file" else ("#fdae6b" if d.get("kind")=="class" else "#c7e9c0") for _, d in G.nodes(data=True)]
    nx.draw(G, pos, with_labels=True, node_size=1400, node_color=node_colors, font_size=8, arrows=True, edge_color="gray")
    plt.title("HPG (Hierarchical Program Graph)")
    out = os.path.join(GRAPH_DIR, "hpg_repo.png")
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    print(f"HPG saved -> {out}")
    return out

# ---------- CFG (Control Flow Graph) ----------

def generate_cfgs(ir_data: Dict[str, Any]):
    print("Generating CFGs...")
    generated = 0
    for file_path, file_ir in ir_data.items():
        basename = os.path.basename(file_path)
        if not isinstance(file_ir, dict):
            continue
        funcs = find_functions_in_ir(file_ir)
        for fnode in funcs:
            fname = fnode.get("name") or "anonymous"
            stmts = extract_statements_from_function(fnode)
            # if no statements, skip (avoid blank images)
            if not stmts:
                # try to use children names as fallback
                if fnode.get("children"):
                    stmts = [safe_label(n.get("type") + ":" + str(n.get("name",""))) for n in fnode.get("children",[])]
                if not stmts:
                    print(f"  CFG skip (no statements) -> {basename} :: {fname}")
                    continue

            G = nx.DiGraph()
            # create nodes for statements
            for i, s in enumerate(stmts):
                node_id = f"S{i}"
                G.add_node(node_id, label=s)
                if i > 0:
                    G.add_edge(f"S{i-1}", node_id)

            # draw
            plt.figure(figsize=(8, max(3, len(stmts)*0.5)))
            pos = nx.spring_layout(G, k=0.5)
            labels = {n: G.nodes[n].get("label", n) for n in G.nodes()}
            nx.draw(G, pos, with_labels=True, labels=labels, node_color="#c6dbef", node_size=1500, font_size=8, arrows=True, edge_color="gray")
            plt.title(f"CFG - {fname} ({basename})", fontsize=10)

            safe_fname = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in fname)[:60]
            out_path = os.path.join(CFG_DIR, f"{basename}_{safe_fname}_cfg.png")
            plt.savefig(out_path, bbox_inches="tight")
            plt.close()
            print(f"  CFG saved -> {out_path}")
            generated += 1
    print(f"CFG generation complete. {generated} graphs created.")
    return generated

# ---------- PDG (Program Dependence Graph) ----------

def generate_pdgs(ir_data: Dict[str, Any]):
    print("Generating PDGs...")
    generated = 0
    for file_path, file_ir in ir_data.items():
        basename = os.path.basename(file_path)
        if not isinstance(file_ir, dict):
            continue
        funcs = find_functions_in_ir(file_ir)
        for fnode in funcs:
            fname = fnode.get("name") or "anonymous"
            defines, uses = extract_var_defs_and_uses(fnode)
            if not defines and not uses:
                print(f"  PDG skip (no defs/uses) -> {basename} :: {fname}")
                continue

            G = nx.DiGraph()
            # add variable nodes
            for v in defines:
                G.add_node(f"DEF::{v}", label=v, kind="def")
            for v in uses:
                G.add_node(f"USE::{v}", label=v, kind="use")

            # link defs -> function and uses -> function (simple PDG)
            func_node = f"FUNC::{basename}::{fname}"
            G.add_node(func_node, label=fname, kind="function")
            for d in defines:
                G.add_edge(f"DEF::{d}", func_node)
            for u in uses:
                # represent use edge from function to variable (or variable to function)
                G.add_edge(func_node, f"USE::{u}")

            plt.figure(figsize=(8, max(3, max(1, (len(defines)+len(uses))*0.3))))
            pos = nx.spring_layout(G, k=0.5)
            labels = {n: G.nodes[n].get("label", n) for n in G.nodes()}
            node_colors = []
            for n, d in G.nodes(data=True):
                kind = d.get("kind")
                if kind == "def":
                    node_colors.append("#a1d99b")
                elif kind == "use":
                    node_colors.append("#fc9272")
                elif kind == "function":
                    node_colors.append("#9ecae1")
                else:
                    node_colors.append("#d9d9d9")

            nx.draw(G, pos, with_labels=True, labels=labels, node_color=node_colors, node_size=1400, font_size=8, arrows=True, edge_color="gray")
            plt.title(f"PDG - {fname} ({basename})", fontsize=10)

            safe_fname = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in fname)[:60]
            out_path = os.path.join(PDG_DIR, f"{basename}_{safe_fname}_pdg.png")
            plt.savefig(out_path, bbox_inches="tight")
            plt.close()
            print(f"  PDG saved -> {out_path}")
            generated += 1
    print(f"PDG generation complete. {generated} graphs created.")
    return generated

# ---------- Main ----------

def main():
    ir_data = load_ir()
    hpg_path = generate_hpg(ir_data)
    cfg_count = generate_cfgs(ir_data)
    pdg_count = generate_pdgs(ir_data)
    print("\nSummary:")
    if hpg_path:
        print(" - HPG:", hpg_path)
    print(f" - CFGs created: {cfg_count}")
    print(f" - PDGs created: {pdg_count}")
    print(f"Graphs are in: {GRAPH_DIR}")

if __name__ == "__main__":
    main()
