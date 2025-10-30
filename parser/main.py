from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from ir_processor import generate_ir_from_repo

app = FastAPI(title="CodeIQ - Intelligent Repo Analyzer")

# Allow React frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Welcome to CodeIQ backend!"}

@app.post("/generate_ir")
def generate_ir(repo_url: str = Query(..., description="GitHub repository URL")):
    """
    API endpoint to generate Intermediate Representation (IR) 
    of all source code files in a GitHub repository.
    """
    result = generate_ir_from_repo(repo_url)
    return {
        "message": "IR generated successfully",
        "files_processed": len(result),
        "data": result
    }

# Run using: uvicorn main:app --reload
