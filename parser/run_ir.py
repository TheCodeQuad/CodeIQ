import os
from typing import Optional

# Supported languages
EXT_LANG = {
    '.c': 'c',
    '.java': 'java',
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
}

# Files/extensions to skip
SKIP_EXT = {
    '.md', '.txt', '.json', '.yml', '.yaml',
    '.xml', '.csv', '.html', '.css', '.lock'
}

SKIP_FILES = {
    '__init__.py',
    'package-lock.json',
    'requirements.txt'
}

def detect_language(file_path: str) -> Optional[str]:
    """Detect programming language based on extension."""
    _, ext = os.path.splitext(file_path)
    return EXT_LANG.get(ext.lower())

def should_skip(file_path: str) -> bool:
    """Return True if file should be ignored."""
    _, ext = os.path.splitext(file_path)
    name = os.path.basename(file_path)
    return name in SKIP_FILES or ext.lower() in SKIP_EXT
