from tree_sitter import Language, Parser

# Load compiled language library
MY_LANG = 'build/my-languages.so'
PY_LANGUAGE = Language(MY_LANG, 'python')

parser = Parser()
parser.set_language(PY_LANGUAGE)

# Sample Python code
code = b"""
def add(a, b):
    return a + b
"""

tree = parser.parse(code)
root_node = tree.root_node

print("Root node type:", root_node.type)
print("Children types:", [child.type for child in root_node.children])
