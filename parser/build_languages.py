from tree_sitter import Language

Language.build_library(
    'build/my-languages.so',
    [
        'tree_sitter_grammars/tree-sitter-python',
        'tree_sitter_grammars/tree-sitter-java',
        'tree_sitter_grammars/tree-sitter-javascript',
        'tree_sitter_grammars/tree-sitter-c',
        'tree_sitter_grammars/tree-sitter-typescript/typescript'
    ]
)
