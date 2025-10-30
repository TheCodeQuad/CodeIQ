"""
Build the Tree-sitter Python language library for tree-sitter 0.25+

This script compiles the tree-sitter-python grammar into a shared library (.dll on Windows)
that can be loaded by the tree-sitter Python bindings.

Usage:
    python build_language.py
"""
import os
import sys
from pathlib import Path

def build_python_language():
    """Build the Python language library using tree-sitter 0.25+ API"""
    
    current_dir = Path(__file__).parent
    grammar_dir = current_dir / "tree-sitter-python"
    build_dir = current_dir / "build"
    
    # Create build directory
    build_dir.mkdir(exist_ok=True)
    
    # Check if grammar exists
    if not grammar_dir.exists():
        print("❌ tree-sitter-python directory not found!")
        print("Please clone it first:")
        print("  git clone https://github.com/tree-sitter/tree-sitter-python.git")
        return False
    
    # Check for src/parser.c
    parser_c = grammar_dir / "src" / "parser.c"
    if not parser_c.exists():
        print(f"❌ Parser source not found at {parser_c}")
        return False
    
    print(f"✅ Found grammar at {grammar_dir}")
    
    # For tree-sitter 0.25+, we need to use the new Language.build_library approach
    # But since that's removed, we'll use ctypes and compile manually
    try:
        import tree_sitter
        print(f"✅ tree-sitter version: {tree_sitter.__version__}")
        
        # Try the new API if available
        if hasattr(tree_sitter, 'Language'):
            from tree_sitter import Language
            
            # The new API expects a compiled .so/.dll
            # We need to compile it using the tree-sitter CLI or manually
            print("\n⚠️  Tree-sitter 0.25+ requires pre-compiled language libraries.")
            print("Please use tree-sitter CLI or install tree-sitter-python package:")
            print("\n  Option 1: Install language package")
            print("    pip install tree-sitter-python")
            print("\n  Option 2: Use tree-sitter CLI")
            print("    npm install -g tree-sitter-cli")
            print("    cd tree-sitter-python")
            print("    tree-sitter build")
            
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = build_python_language()
    sys.exit(0 if success else 1)
