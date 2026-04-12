import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class WorkspaceProvider:
    def __init__(self, base_root: str):
        self.base_root = Path(base_root).expanduser().resolve()
        os.makedirs(self.base_root, exist_ok=True)

    def get_workspace_root(self, user_id: str = "default", agent_id: str = "agent_1") -> Path:
        path = self.base_root / user_id / agent_id
        os.makedirs(path, exist_ok=True)
        # Create subdirs
        os.makedirs(path / "logs", exist_ok=True)
        os.makedirs(path / "memory", exist_ok=True)
        os.makedirs(path / "skills", exist_ok=True)
        return path

    def append_log(self, workspace_root: Path, filename: str, content: str):
        log_path = workspace_root / "logs" / filename
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(content + "\n")
