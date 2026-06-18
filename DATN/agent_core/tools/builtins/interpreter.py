import logging
import sys
import io
import contextlib
from pathlib import Path

logger = logging.getLogger(__name__)

_interpreter_globals = {"__builtins__": __builtins__}

try:
    current_file = Path(__file__).resolve()
    lib_path = current_file.parent.parent / "python_lib"
    
    if str(lib_path) not in sys.path:
        sys.path.append(str(lib_path))
        
    import fin_lib
    _interpreter_globals["fin_lib"] = fin_lib
    logger.info(f"Standardized financial library (fin_lib) loaded from {lib_path}")
except Exception as e:
    logger.error(f"Failed to load financial library: {e}")

async def python_interpreter(code: str) -> str:
    """
    Executes Python code in a persistent environment and returns the output.
    """
    dangerous = ["os", "sys", "shutil", "subprocess", "socket"]
    if any(f"import {d}" in code or f"from {d}" in code for d in dangerous):
        return "Error: Use of restricted modules detected."

    stdout = io.StringIO()
    stderr = io.StringIO()
    
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(code, _interpreter_globals)
        
        output = stdout.getvalue()
        errors = stderr.getvalue()
        
        if errors:
            result = f"Output:\n{output}\nErrors:\n{errors}"
        else:
            result = output if output else "Code executed successfully."
            
        return result
    except Exception as e:
        return f"Execution Error: {str(e)}"
