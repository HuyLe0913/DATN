import os
import logging

logger = logging.getLogger(__name__)

async def read_file(path: str) -> str:
    """Read content from a file."""
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' not found."
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        return f"Error reading file: {str(e)}"
