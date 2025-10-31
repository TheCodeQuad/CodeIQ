from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import os, json, subprocess, sys
import sys, shutil


# ✅ Import your navigator modules
from navigator.repo_cloner import clone_repository

app = FastAPI(title="CodeIQ Backend")

# ----------CORS CONFIG----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later: ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- BASE PATHS ----------
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
NAVIGATOR_DIR = os.path.join(BASE_DIR, "navigator", "parsers")
os.makedirs(DATA_DIR, exist_ok=True)

# ---------- MODELS ----------
class RepoRequest(BaseModel):
    repo_url: str
    threshold: int = 4  # Default importance threshold for file selection


# ---------- ROUTES ----------
@app.get("/")
def home():
    return {"message": "Welcome to CodeIQ Backend"}


@app.post("/navigator/start")
async def start_navigation(request: RepoRequest):
    """
    Clone a GitHub repository and generate an IR summary for it.
    """
    try:
        repo_url = request.repo_url.strip()
        if not repo_url:
            raise HTTPException(status_code=400, detail="Repository URL is required")

        # ✅ Clone the repository to /data
        try:
            local_path = clone_repository(repo_url, DATA_DIR)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Clone failed: {str(e)}")

        # ✅ Path to IR builder
        script_path = os.path.join(BASE_DIR, "navigator", "parsers", "ir_builder.py")

        # ✅ Run the IR builder with threshold parameter (filters only important files)
        threshold = request.threshold if hasattr(request, 'threshold') else 4
        result = subprocess.run(
            [sys.executable, script_path, local_path, str(threshold)],  # Pass threshold to filter files
            cwd=BASE_DIR,  # Run from backend root for proper imports
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(f"IR generation failed:\n{result.stderr}")

        # ✅ Get the repo name for loading the generated IR
        repo_name = os.path.basename(local_path)
        repo_ir_path = os.path.join(DATA_DIR, "IR", repo_name, "repo", f"{repo_name}_repo.json")
        
        if not os.path.exists(repo_ir_path):
            raise Exception(f"IR output not found at {repo_ir_path}")

        with open(repo_ir_path, "r", encoding="utf-8") as f:
            ir_data = json.load(f)


        # ✅ Load the selection manifest to show what was filtered
        manifest_path = os.path.join(DATA_DIR, "IR", repo_name, "repo", "selected_files.json")
        selection_info = {}
        selected_files_list = []
        excluded_files_list = []
        
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                selected_files_list = manifest.get("selected", [])
                excluded_files_list = manifest.get("excluded", [])
                selection_info = {
                    "selected_count": len(selected_files_list),
                    "excluded_count": len(excluded_files_list),
                    "threshold": threshold,
                    "selected_files": selected_files_list,
                    "excluded_files": excluded_files_list[:20]  # Limit to first 20 for display
                }

        # ✅ Calculate detailed statistics from IR data
        total_functions = len(ir_data.get("files", []))
        total_classes = 0
        total_imports = len(set(ir_data.get("dependencies", [])))
        
        # Count functions and classes across all files
        function_count = 0
        class_count = 0
        for file_info in ir_data.get("files", []):
            functions_list = file_info.get("functions", [])
            function_count += len(functions_list)
        
        # Count function JSONs in the functions folder
        functions_dir = os.path.join(DATA_DIR, "IR", repo_name, "functions")
        if os.path.exists(functions_dir):
            function_json_count = len([f for f in os.listdir(functions_dir) if f.endswith('.json')])
        else:
            function_json_count = 0

        stats = {
            "files_analyzed": len(ir_data.get("files", [])),
            "total_functions": function_json_count,
            "total_classes": class_count,
            "total_imports": total_imports,
            "entry_points": len(ir_data.get("entry_points", []))
        }

        # ✅ Combine repo info + IR result + filtering info + stats
        response = {
            "status": "success",
            "message": f"Repository cloned and analyzed. {selection_info.get('selected_count', 0)} important files selected.",
            "repo_path": local_path,
            "repo_name": repo_name,
            "filtering": selection_info,
            "statistics": stats,
            "ir": ir_data,
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate_ir")
def generate_ir():
    """
    Directly trigger IR generation without cloning (for already downloaded code).
    """
    try:
        script_path = os.path.join(BASE_DIR, "navigator", "parsers", "ir_builder.py")

        result = subprocess.run(
            ["python", script_path],
            cwd=NAVIGATOR_DIR,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(result.stderr)

        ir_output_path = os.path.join(NAVIGATOR_DIR, "ir_output.json")
        if not os.path.exists(ir_output_path):
            raise Exception("IR output not found.")

        with open(ir_output_path, "r", encoding="utf-8") as f:
            ir_data = json.load(f)

        return {"status": "success", "ir": ir_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/navigator/generate_cfg")
async def generate_cfg(request: dict):
    """
    Generate CFG for a specific file from analyzed repository
    """
    try:
        repo_name = request.get("repo_name")
        file_path = request.get("file_path")  # Relative path within repo
        
        if not repo_name or not file_path:
            raise HTTPException(status_code=400, detail="repo_name and file_path are required")
        
        # Get the actual file path
        repo_files_dir = os.path.join(DATA_DIR, "IR", repo_name, "repo_files")
        full_file_path = os.path.join(repo_files_dir, file_path)
        
        if not os.path.exists(full_file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        # Generate CFG JSON
        cfg_generator_script = os.path.join(BASE_DIR, "navigator", "graph_builders", "cfg_generator.py")
        cfg_output_dir = os.path.join(DATA_DIR, "IR", repo_name, "cfg")
        os.makedirs(cfg_output_dir, exist_ok=True)
        
        # Create safe filename
        safe_filename = file_path.replace('/', '_').replace('\\', '_').replace('.py', '')
        cfg_json_path = os.path.join(cfg_output_dir, f"{safe_filename}_cfg.json")
        
        result = subprocess.run(
            [sys.executable, cfg_generator_script, full_file_path, cfg_json_path],
            cwd=os.path.dirname(cfg_generator_script),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"CFG generation failed: {result.stderr}")
        
        # Generate HTML visualization
        cfg_visualizer_script = os.path.join(BASE_DIR, "navigator", "graph_builders", "cfg_visualizer.py")
        cfg_html_path = os.path.join(cfg_output_dir, f"{safe_filename}_cfg.html")
        
        result = subprocess.run(
            [sys.executable, cfg_visualizer_script, cfg_json_path, cfg_html_path],
            cwd=os.path.dirname(cfg_visualizer_script),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"CFG visualization failed: {result.stderr}")
        
        # Load CFG data
        with open(cfg_json_path, 'r', encoding='utf-8') as f:
            cfg_data = json.load(f)
        
        return {
            "status": "success",
            "message": "CFG generated successfully",
            "cfg_json_path": cfg_json_path,
            "cfg_html_path": cfg_html_path,
            "cfg_data": cfg_data,
            "html_url": f"/cfg/{repo_name}/{safe_filename}_cfg.html"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cfg/{repo_name}/{filename}")
async def serve_cfg_html(repo_name: str, filename: str):
    """
    Serve CFG HTML visualization files
    """
    try:
        cfg_path = os.path.join(DATA_DIR, "IR", repo_name, "cfg", filename)
        
        if not os.path.exists(cfg_path):
            raise HTTPException(status_code=404, detail="CFG file not found")
        
        return FileResponse(cfg_path, media_type="text/html")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
