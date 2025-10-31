import sys, os, json

# Debug: print Python info
print(f"Python executable: {sys.executable}", file=sys.stderr)
print(f"Python version: {sys.version}", file=sys.stderr)
print(f"Working directory: {os.getcwd()}", file=sys.stderr)

from python_parser import parse_python_repo  # your custom parser function

def main():
    if len(sys.argv) < 2:
        print(" Usage: python ir_builder.py <repo_path>")
        sys.exit(1)

    repo_path = sys.argv[1]
    print(f" Building IR for repository at: {repo_path}")

    # Parse all Python files and build IR
    ir = parse_python_repo(repo_path)

    # Save IR
    output_path = os.path.join(os.path.dirname(__file__), "ir_output.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ir, f, indent=2)

    print(f"IR saved at: {output_path}")
    

if __name__ == "__main__":
    main()
