import os
from tree_sitter import Language, Parser

# Load compiled library
MY_LANG = 'build/my-languages.so'
Language.build_library(
    MY_LANG,
    [
        'tree_sitter_grammars/tree-sitter-python',
        'tree_sitter_grammars/tree-sitter-java',
        'tree_sitter_grammars/tree-sitter-javascript',
        'tree_sitter_grammars/tree-sitter-c',
        'tree_sitter_grammars/tree-sitter-typescript/typescript'
    ]
)

# Load languages
PY_LANGUAGE = Language(MY_LANG, 'python')
JAVA_LANGUAGE = Language(MY_LANG, 'java')
JS_LANGUAGE = Language(MY_LANG, 'javascript')
C_LANGUAGE = Language(MY_LANG, 'c')
TS_LANGUAGE = Language(MY_LANG, 'typescript')

# Map file extensions to languages
EXT_LANG_MAP = {
    '.py': PY_LANGUAGE,
    '.java': JAVA_LANGUAGE,
    '.js': JS_LANGUAGE,
    '.c': C_LANGUAGE,
    '.ts': TS_LANGUAGE,
}

# Folder containing files to parse
SOURCE_DIR = '../source_files/flask_app'

parser = Parser()

# Parse all files
for filename in os.listdir(SOURCE_DIR):
    file_path = os.path.join(SOURCE_DIR, filename)
    ext = os.path.splitext(filename)[1]
    
    if ext in EXT_LANG_MAP:
        parser.set_language(EXT_LANG_MAP[ext])
        
        with open(file_path, 'rb') as f:
            code = f.read()
        
        tree = parser.parse(code)
        root_node = tree.root_node
        
        print(f"\nFile: {filename}")
        print("Root node type:", root_node.type)
        print("Children types:", [child.type for child in root_node.children])
