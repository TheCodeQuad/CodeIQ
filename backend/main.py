from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, json, subprocess, sys  # ✅ added sys here\
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

        # ✅ Run the IR builder and pass repo path argument
        result = subprocess.run(
    [sys.executable, script_path, local_path],  # ✅ ensures it uses the same venv python
    cwd=NAVIGATOR_DIR,
    capture_output=True,
    text=True
)

        if result.returncode != 0:
            raise Exception(f"IR generation failed:\n{result.stderr}")

        # ✅ Load generated IR output
        ir_output_path = os.path.join(NAVIGATOR_DIR, "ir_output.json")
        if not os.path.exists(ir_output_path):
            raise Exception("IR output not found after generation.")

        with open(ir_output_path, "r", encoding="utf-8") as f:
            ir_data = json.load(f)


        # ✅ Combine repo info + IR result
        response = {
            "status": "success",
            "message": "Repository cloned and IR generated successfully.",
            "repo_path": local_path,
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
