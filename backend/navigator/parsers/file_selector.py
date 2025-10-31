import os
import ast
import json
import sys

# Fix encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Hardcoded exclusions - these are folder names to skip during traversal
EXCLUDE_DIRS = {"tests", "test", "examples", "docs", "venv", ".venv", "__pycache__", "node_modules", ".git"}

def is_excluded(path, repo_path=None):
    """Exclude paths that belong to irrelevant folders."""
    # Get the path parts relative to repo root if available
    if repo_path:
        try:
            rel_path = os.path.relpath(path, repo_path)
            parts = rel_path.replace("\\", "/").split("/")
        except ValueError:
            parts = path.replace("\\", "/").split("/")
    else:
        parts = path.replace("\\", "/").split("/")
    
    # Check if any directory component (not the filename) is in exclusion list
    dir_parts = parts[:-1]  # Exclude the filename itself
    return any(part in EXCLUDE_DIRS for part in dir_parts)

def quick_ast_scan(filepath):
    """Return quick AST stats for scoring."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
        tree = ast.parse(code)
        func_count = sum(isinstance(n, ast.FunctionDef) for n in ast.walk(tree))
        class_count = sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree))
        has_main = any(
            isinstance(n, ast.If)
            and isinstance(n.test, ast.Compare)
            and hasattr(n.test.left, "id")
            and n.test.left.id == "__name__"
            for n in ast.walk(tree)
        )
        loc = len(code.splitlines())
        return {"funcs": func_count, "classes": class_count, "has_main": has_main, "loc": loc}
    except Exception:
        return {"funcs": 0, "classes": 0, "has_main": False, "loc": 0}

def score_file(filepath, repo_path=None):
    """Score file importance."""
    score = 0
    filename = os.path.basename(filepath)

    if is_excluded(filepath, repo_path):
        return -999  # force skip

    # Exclude test files by naming pattern
    if filename.startswith("test_") or filename == "test.py" or "test" in filename.lower():
        return -999
    
    # Exclude setup/config/version files
    if filename in {"setup.py", "setup.cfg", "version.py", "versions.py", "_version.py"}:
        return -999

    stats = quick_ast_scan(filepath)

    # Inside main package folder (any nested .py files inside repo)
    # Check if file is in a package directory (has parent __init__.py or is nested)
    if repo_path:
        try:
            rel_path = os.path.relpath(filepath, repo_path)
            path_parts = rel_path.split(os.sep)
            # If file is nested (not at root), likely part of main package
            if len(path_parts) > 1:
                score += 3
        except ValueError:
            pass
    
    # Functions/classes
    score += 2 * (stats["funcs"] + stats["classes"])
    if stats["funcs"] + stats["classes"] > 3:
        score += 2

    # Non-trivial size
    if stats["loc"] > 15:
        score += 1

    # Entrypoints
    if stats["has_main"] or "__main__" in filename:
        score += 3

    # Filename priority
    if filename in {"__init__.py", "core.py", "main.py"}:
        score += 1

    return score

def select_important_files(repo_path, threshold=4, preview=False):
    """Select and optionally preview files above threshold."""
    selected = []
    excluded = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                score = score_file(path, repo_path)  # Pass repo_path for relative path calculation
                if score >= threshold:
                    selected.append({"path": path, "score": score})
                else:
                    excluded.append({"path": path, "score": score})

    # Save manifest to the IR output directory
    repo_name = os.path.basename(repo_path)
    # Calculate the data/IR path relative to this script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(os.path.dirname(script_dir))  # Go up to backend/
    manifest_dir = os.path.join(backend_dir, "data", "IR", repo_name, "repo")
    os.makedirs(manifest_dir, exist_ok=True)
    manifest_path = os.path.join(manifest_dir, "selected_files.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"selected": selected, "excluded": excluded}, f, indent=4)

    if preview:
        print(f"\n✅ Selected {len(selected)} files (threshold={threshold}):")
        for s in sorted(selected, key=lambda x: -x["score"])[:10]:
            print(f"  + {s['path']} (score={s['score']})")

        print(f"\n🚫 Excluded {len(excluded)} files:")
        for e in sorted(excluded, key=lambda x: x["score"])[:10]:
            print(f"  - {e['path']} (score={e['score']})")

    return [f["path"] for f in selected]
