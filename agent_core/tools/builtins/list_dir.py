import os
import logging

logger = logging.getLogger(__name__)

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
        logger.error(f"Error listing directory {path}: {e}")
        return f"Error listing directory: {str(e)}"
