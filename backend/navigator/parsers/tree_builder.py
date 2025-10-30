"""
Tree-sitter language builder (DEPRECATED for tree-sitter >= 0.25.0)

With tree-sitter 0.25+, you no longer need to build language libraries.
The Language class can load grammars directly from the tree-sitter-python repository.

Simply ensure you have:
1. tree-sitter >= 0.25.0 installed: pip install tree-sitter>=0.25.0
2. tree-sitter-python cloned in the same directory as this file

The new API is used in python_parser.py:
    PY_LANGUAGE = Language(str(LANG_DIR), "python")
    parser = Parser(PY_LANGUAGE)

No compilation step needed!
"""
print("⚠️  This script is deprecated for tree-sitter >= 0.25.0")
print("✅ Language grammars are now loaded directly without compilation.")
print("   See python_parser.py for the new API usage.")
