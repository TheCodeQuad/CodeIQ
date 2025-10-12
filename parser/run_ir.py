import os
import json
from ir_builder import parse_file, detect_language

SOURCE_DIR = '../source_files'
OUTPUT_JSON = 'ir_output.json'
SKIP_DIRS = {'venv', '__pycache__'}  # directories to skip

all_ir = {}

for root, dirs, files in os.walk(SOURCE_DIR):
    # Skip unwanted directories
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

    for file in files:
        file_path = os.path.join(root, file)
        lang = detect_language(file_path)
        if not lang:
            continue
        print(f"Parsing {file_path} as {lang}")
        ir_tree = parse_file(file_path, lang)
        all_ir[file_path] = ir_tree.to_dict()

with open(OUTPUT_JSON, 'w') as f:
    json.dump(all_ir, f, indent=4)

print(f"IR JSON saved to {OUTPUT_JSON}")
