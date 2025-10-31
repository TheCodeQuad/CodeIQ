import sys
import os
import json
import shutil
from pathlib import Path

# --- Ensure root folder is in sys.path ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)  # this is the backend/navigator folder
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from parsers.python_parser import parse_python_file, parse_python_repo  # uses your parser logic

# ====================================================
# LAYERED IR BUILDER
# ====================================================

def ensure_dirs(base_dir: Path):
    """Ensure the per-repo IR directory structure exists.

    Creates the following under base_dir:
      - repo_files/   (copied source files, preserving relative paths)
      - files/        (per-file IR JSON)
      - functions/    (per-function JSON)
      - repo/         (repo-level summary JSON)
    """
    paths = [
        base_dir / "repo_files",
        base_dir / "files",
        base_dir / "functions",
        base_dir / "repo",
    ]
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)

def build_layered_ir(repo_path):
    """Walk through repo and generate layered IR files."""
    repo_name = Path(repo_path).name
    # Use uppercase IR folder as requested: data/IR/<repo_name>/
    data_root = Path(__file__).resolve().parent.parent.parent / "data"
    base_dir = data_root / "IR" / repo_name
    ensure_dirs(base_dir)

    repo_ir = {
        "repo": repo_name,
        "path": repo_path,
        "files": [],
        "dependencies": [],
        "entry_points": []
    }

    skip_dirs = {"venv", "__pycache__", "build", "dist", ".git", "node_modules", ".mypy_cache"}

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)
            try:
                file_ir = parse_python_file(file_path)

                # --- Save File-Level IR ---
                rel_path = Path(file_path).relative_to(Path(repo_path))
                file_name = rel_path.with_suffix("").as_posix().replace('/', '__')
                file_out = base_dir / "files" / f"{file_name}.json"
                with open(file_out, "w", encoding="utf-8") as f:
                    json.dump(file_ir, f, indent=2, ensure_ascii=False)

                # --- Save Function-Level IRs (one file per function) ---
                funcs = file_ir.get("functions", [])
                for idx, func in enumerate(funcs):
                    func_name = func.get("name") or f"anonymous_{idx}"
                    safe_name = f"{file_name}__{func_name}"
                    func_out = base_dir / "functions" / f"{safe_name}.json"
                    with open(func_out, "w", encoding="utf-8") as f:
                        json.dump(func, f, indent=2, ensure_ascii=False)

                # --- Copy source file into repo_files preserving relative path ---
                dest_file = base_dir / "repo_files" / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(file_path, dest_file)
                except Exception:
                    # ignore copy failures but continue
                    pass

                # --- Append File Info to Repo IR ---
                repo_ir["files"].append({
                    "path": str(rel_path),
                    "file_ir": str(file_out.relative_to(base_dir)),
                    "functions": [f.get("name") for f in funcs]
                })

                # --- Collect dependencies ---
                repo_ir["dependencies"].extend(file_ir.get("imports", []))

            except Exception as e:
                print(f" Error parsing {file_path}: {e}", file=sys.stderr)

    # --- Save Repo-Level IR ---
    repo_out = base_dir / "repo" / f"{repo_name}_repo.json"
    with open(repo_out, "w", encoding="utf-8") as f:
        json.dump(repo_ir, f, indent=2, ensure_ascii=False)

    print(f"\n Repo IR saved at: {repo_out}")
    print(f"Total files parsed: {len(repo_ir['files'])}")
    print(f" IR folders created under: {base_dir}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python ir_builder.py <repo_path>")
        sys.exit(1)

    repo_path = sys.argv[1]
    if not os.path.isdir(repo_path):
        print(f" Invalid path: {repo_path}")
        sys.exit(1)

    print(f" Building layered IR for repo: {repo_path}")
    build_layered_ir(repo_path)

if __name__ == "__main__":
    main()
