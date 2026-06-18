import yaml
import logging
from pathlib import Path
from typing import List, Set, Dict, Any

logger = logging.getLogger(__name__)

class PolicyManager:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.allowlist: Set[str] = set()
        self.denylist: Set[str] = set()
        self.enabled: bool = False

    def load_policy(self, agent_id: str):
        """Loads POLICY.yaml for the specified agent."""
        policy_path = self.workspace_root / agent_id / "POLICY.yaml"
        if not policy_path.exists():
            logger.warning(f"Policy file not found for agent {agent_id}: {policy_path}. All tools allowed by default.")
            self.enabled = False
            return

        try:
            with open(policy_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                
            tool_perms = config.get("tool_permissions", {})
            self.enabled = tool_perms.get("enabled", False)
            self.allowlist = set(item.strip() for item in tool_perms.get("allowlist", []))
            self.denylist = set(item.strip() for item in tool_perms.get("denylist", []))
            
            logger.info(f"Loaded policy for {agent_id}: {len(self.allowlist)} allowed, {len(self.denylist)} denied.")
        except Exception as e:
            logger.error(f"Error loading policy for {agent_id}: {e}")
            self.enabled = False

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Checks if a tool is allowed under the current policy."""
        if not self.enabled:
            return True
            
        if tool_name in self.denylist:
            return False

        if self.allowlist:
            return tool_name in self.allowlist
            
        return True
