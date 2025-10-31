# import os
# import json
# from pathlib import Path
# from navigator.parsers.python_parser import parse_python_file
# from navigator.repo_cloner import clone_repo
# from navigator.file_selector import select_files  # ✅ new import

# def build_ir(repo_path, output_path="ir_output.json", threshold=4):
#     print("\n🔍 Selecting important files from repository...")
#     scored, selected = select_files(repo_path, threshold)

#     selected_paths = [f["path"] for f in selected]
#     print(f"\n✅ {len(selected_paths)} important files selected out of {len(scored)} total.\n")

#     ir_data = {}

#     for file_path in selected_paths:
#         try:
#             tree_json = parse_python_file(file_path)
#             ir_data[file_path] = tree_json
#             print(f"✅ Parsed: {file_path}")
#         except Exception as e:
#             print(f"❌ Failed to parse {file_path}: {e}")

#     with open(output_path, "w", encoding="utf-8") as f:
#         json.dump(ir_data, f, indent=2)

#     print(f"\n🎯 Filtered IR generated and saved to {output_path}")

# if __name__ == "__main__":
#     repo_url = input("Enter Python repo URL: ").strip()
#     threshold = int(input("Enter importance threshold (default 4): ") or 4)
#     local_path = clone_repo(repo_url)
#     build_ir(local_path, threshold=threshold)
