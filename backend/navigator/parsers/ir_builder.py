import sys
import os
import json
import shutil
from pathlib import Path

# Fix encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# --- Ensure root folder is in sys.path ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))  # Go up to backend/
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from navigator.parsers.python_parser import parse_python_file
from navigator.parsers.file_selector import select_important_files  # <== integrate filtering here

# ====================================================
# LAYERED IR BUILDER (with filtering)
# ====================================================

def ensure_dirs(base_dir: Path):
    """Ensure the per-repo IR directory structure exists."""
    paths = [
        base_dir / "repo_files",
        base_dir / "files",
        base_dir / "functions",
        base_dir / "repo",
    ]
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def build_layered_ir(repo_path, threshold=4):
    """Walk through repo and generate layered IR files for important modules."""
    repo_name = Path(repo_path).name
    data_root = Path(__file__).resolve().parent.parent.parent / "data"
    base_dir = data_root / "IR" / repo_name
    ensure_dirs(base_dir)

    # --- Step 1: Select important files ---
    print(f"🔍 Selecting important files in {repo_path} (threshold={threshold})...")
    important_files = select_important_files(repo_path, threshold=threshold, preview=True)

    if not important_files:
        print("⚠️ No files passed importance threshold — exiting.")
        return

    # --- Step 2: Initialize repo-level structure ---
    repo_ir = {
        "repo": repo_name,
        "path": repo_path,
        "files": [],
        "dependencies": [],
        "entry_points": []
    }

    # --- Step 3: Parse selected files only ---
    for file_path in important_files:
        try:
            file_ir = parse_python_file(file_path)
            rel_path = Path(file_path).relative_to(Path(repo_path))
            file_name = rel_path.with_suffix("").as_posix().replace('/', '__')

            # --- Save File-Level IR ---
            file_out = base_dir / "files" / f"{file_name}.json"
            with open(file_out, "w", encoding="utf-8") as f:
                json.dump(file_ir, f, indent=2, ensure_ascii=False)

            # --- Save Function-Level IRs ---
            funcs = file_ir.get("functions", [])
            for idx, func in enumerate(funcs):
                func_name = func.get("name") or f"anonymous_{idx}"
                safe_name = f"{file_name}__{func_name}"
                func_out = base_dir / "functions" / f"{safe_name}.json"
                with open(func_out, "w", encoding="utf-8") as f:
                    json.dump(func, f, indent=2, ensure_ascii=False)

            # --- Copy Source File into repo_files ---
            dest_file = base_dir / "repo_files" / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, dest_file)

            # --- Add File Info to Repo IR ---
            repo_ir["files"].append({
                "path": str(rel_path),
                "file_ir": str(file_out.relative_to(base_dir)),
                "functions": [f.get("name") for f in funcs]
            })

            # --- Collect dependencies ---
            repo_ir["dependencies"].extend(file_ir.get("imports", []))

            print(f"✅ Parsed: {file_path}")

        except Exception as e:
            print(f"❌ Failed to parse {file_path}: {e}", file=sys.stderr)

    # --- Step 4: Save Repo-Level IR ---
    repo_out = base_dir / "repo" / f"{repo_name}_repo.json"
    with open(repo_out, "w", encoding="utf-8") as f:
        json.dump(repo_ir, f, indent=2, ensure_ascii=False)

    print(f"\n🎯 Repo IR saved at: {repo_out}")
    print(f"📄 Total important files parsed: {len(repo_ir['files'])}")
    print(f"📁 IR folders created under: {base_dir}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python ir_builder.py <repo_path> [threshold]")
        sys.exit(1)

    repo_path = sys.argv[1]
    threshold = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    if not os.path.isdir(repo_path):
        print(f"❌ Invalid path: {repo_path}")
        sys.exit(1)

    print(f"🚀 Building filtered layered IR for repo: {repo_path}")
    build_layered_ir(repo_path, threshold=threshold)


if __name__ == "__main__":
    main()
