import os
import logging

logger = logging.getLogger(__name__)

async def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to '{path}'."
    except Exception as e:
        logger.error(f"Error writing file {path}: {e}")
        return f"Error writing file: {str(e)}"
