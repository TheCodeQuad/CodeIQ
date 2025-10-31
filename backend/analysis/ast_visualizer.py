import json, os, sys

def build_html_tree(data):
    if isinstance(data, dict):
        html = "<ul>"
        for key, value in data.items():
            html += f"<li><span class='node' onclick='toggleNode(event)'>{key}</span>"
            html += f"<div class='children hidden'>{build_html_tree(value)}</div></li>"
        html += "</ul>"
        return html
    elif isinstance(data, list):
        return "<ul>" + "".join([f"<li>{build_html_tree(item)}</li>" for item in data]) + "</ul>"
    else:
        return f"<span class='value'>{repr(data)}</span>"

def visualize_ast(json_path, output_html_path, template_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        ast_data = json.load(f)

    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    tree_html = build_html_tree(ast_data)
    html_content = template.replace("{{title}}", os.path.basename(json_path)) \
                           .replace("{{tree_html}}", tree_html)

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_html_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ AST visualization stored at: {output_html_path}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python ast_visualizer.py <ast.json> <output.html> <template.html>")
        sys.exit(1)

    visualize_ast(sys.argv[1], sys.argv[2], sys.argv[3])
