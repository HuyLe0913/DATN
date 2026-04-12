import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

async def read_file(path: str) -> str:
    """Read content from a file."""
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' not found."
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

async def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to '{path}'."
    except Exception as e:
        return f"Error writing file: {str(e)}"

async def list_dir(path: str = ".") -> str:
    """List files and directories in a given path."""
    try:
        items = os.listdir(path)
        if not items:
            return f"Directory '{path}' is empty."
        
        result = [f"Contents of '{path}':"]
        for item in items:
            prefix = "[DIR] " if os.path.isdir(os.path.join(path, item)) else "[FILE]"
            result.append(f"{prefix} {item}")
        return "\n".join(result)
    except Exception as e:
        return f"Error listing directory: {str(e)}"
