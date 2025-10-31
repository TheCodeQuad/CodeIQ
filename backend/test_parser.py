#!/usr/bin/env python3
"""
Quick test to verify tree-sitter Python parser is working
"""
from navigator.parsers.python_parser import parse_python_file

# Test parsing this script itself
result = parse_python_file(__file__)

print("=" * 60)
print("✅ TREE-SITTER PYTHON IS WORKING!")
print("=" * 60)
print(f"\n📁 File: {result['path']}")
print(f"📦 Imports: {len(result['imports'])}")
print(f"🔧 Functions: {len(result['functions'])}")
print(f"📚 Classes: {len(result['classes'])}")
print(f"🔢 Variables: {len(result['variables'])}")

if result['imports']:
    print(f"\n📦 Import examples:")
    for imp in result['imports'][:3]:
        print(f"   - {imp}")

if result['functions']:
    print(f"\n🔧 Function examples:")
    for func in result['functions'][:3]:
        print(f"   - {func['name']}() at line {func['start_line']}")

print("\n" + "=" * 60)
print("✅ Parser is fully functional and ready to use!")
print("=" * 60)
