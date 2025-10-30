import os
import tempfile
import shutil
import json
from typing import Dict, Any
from git import Repo
from ir_builder import parse_file
from run_ir import detect_language, should_skip

# Directories to skip
SKIP_DIRS = {'.git', 'node_modules', 'venv', '__pycache__', 'dist', 'build'}

# 🔥 Folder to store output
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def clone_repo(repo_url: str) -> str:
    """Clone the given GitHub repository into a temporary directory."""
    tmpdir = tempfile.mkdtemp(prefix="codeiq_repo_")
    try:
        print(f"📦 Cloning repository: {repo_url}")
        Repo.clone_from(repo_url, tmpdir)
        print(f"✅ Repository cloned to: {tmpdir}")
        return tmpdir
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise RuntimeError(f"Failed to clone repository: {e}")

def collect_files(root_dir: str):
    """Recursively collect source files from the given directory."""
    files = []
    for root, dirs, filenames in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in filenames:
            full_path = os.path.join(root, f)
            if should_skip(full_path):
                continue
            if detect_language(full_path):
                files.append(full_path)
    return files

def build_ir_for_repo_path(path: str) -> Dict[str, Any]:
    """Generate IR for all valid source files inside the directory."""
    all_ir = {}
    files = collect_files(path)
    print(f"🧩 Found {len(files)} source files to analyze.")

    for fp in files:
        lang = detect_language(fp)
        if not lang:
            continue

        print(f"⚙️ Parsing {fp} ({lang})")

        try:
            ir_node = parse_file(fp, lang)
            all_ir[fp] = ir_node.to_dict()
        except Exception as e:
            all_ir[fp] = {"error": str(e)}

    return all_ir

def generate_ir_from_repo(repo_url: str, cleanup: bool = True) -> Dict[str, Any]:
    """Clone remote repo → generate IR → save as JSON → return info."""
    repo_path = clone_repo(repo_url)
    try:
        ir = build_ir_for_repo_path(repo_path)

        # 🔥 Save IR output to local JSON file
        output_path = os.path.join(OUTPUT_DIR, "ir_output.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(ir, f, indent=2)
        print(f"💾 IR output saved to {output_path}")

        return {
            "status": "success",
            "message": "IR generated and stored successfully",
            "files_processed": len(ir),
            "output_path": output_path,
            "data": ir
        }

    finally:
        if cleanup:
            shutil.rmtree(repo_path, ignore_errors=True)
            print(f"🧹 Cleaned up cloned repository at {repo_path}")

def generate_ir_from_local(path: str) -> Dict[str, Any]:
    """Generate IR for a local repository path."""
    ir = build_ir_for_repo_path(path)

    # 🔥 Also save locally when analyzing local repo
    output_path = os.path.join(OUTPUT_DIR, "ir_output.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ir, f, indent=2)

    print(f"💾 IR output saved to {output_path}")
    return ir

if __name__ == "__main__":
    url = input("Enter GitHub repo URL: ").strip()
    results = generate_ir_from_repo(url)
    print(json.dumps(results, indent=2))
