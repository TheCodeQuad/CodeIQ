# ir_builder.py
import os
import json
from pathlib import Path
from parsers.python_parser import parse_python_file
from repo_cloner import clone_repo

def build_ir(repo_path, output_path="ir_output.json"):
    ir_data = {}

    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    tree_json = parse_python_file(file_path)
                    ir_data[file_path] = tree_json
                    print(f"✅ Parsed: {file_path}")
                except Exception as e:
                    print(f"❌ Failed to parse {file_path}: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ir_data, f, indent=2)

    print(f"\n🎯 IR generated and saved to {output_path}")

if __name__ == "__main__":
    repo_url = input("Enter Python repo URL: ").strip()
    local_path = clone_repo(repo_url)
    build_ir(local_path)
