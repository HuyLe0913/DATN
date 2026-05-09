import os
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SkillMetadata:
    def __init__(self, name: str, description: str, tools: List[str], path: str):
        self.name = name
        self.description = description
        self.tools = tools
        self.path = path
        self.content = ""

class SkillLoader:
    def __init__(self, skills_root: str):
        self.skills_root = Path(skills_root)
        self.skills: Dict[str, SkillMetadata] = {}

    def load_all(self, agent_id: str):
        """
        Scan and load all skills for a specific agent.
        Expected structure: skills_root / agent_id / skills / skill_name / SKILL.md
        """
        agent_skills_dir = self.skills_root / agent_id / "skills"
        if not agent_skills_dir.exists():
            logger.warning(f"Agent skills directory not found: {agent_skills_dir}")
            return

        for skill_dir in agent_skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    self._load_skill_file(skill_file, agent_id)

    def _load_skill_file(self, file_path: Path, agent_id: str):
        try:
            content = file_path.read_text(encoding="utf-8")
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    yaml_content = parts[1]
                    body_content = parts[2]
                    
                    metadata = yaml.safe_load(yaml_content)
                    skill = SkillMetadata(
                        name=metadata.get("name"),
                        description=metadata.get("description"),
                        tools=metadata.get("tools", []),
                        path=str(file_path)
                    )
                    skill.content = body_content.strip()
                    
                    self.skills[skill.name] = skill
                    logger.info(f"Loaded skill: {skill.name} for {agent_id}")
        except Exception as e:
            logger.error(f"Error loading skill file {file_path}: {e}")

    def get_skills_summary(self) -> str:
        """Returns a summarized string of all loaded skills for the system prompt."""
        if not self.skills:
            return "No specialized skills available."
        
        summary = ["### CÁC KỸ NĂNG CHUYÊN SÂU (BẮT BUỘC TUÂN THỦ PROCEDURES):"]
        for name, skill in self.skills.items():
            summary.append(f"\n#### Skill: {name}")
            summary.append(f"Mô tả: {skill.description}")
            summary.append(f"Hướng dẫn thực hiện:\n{skill.content}")
        return "\n".join(summary)

    def get_skill_detail(self, skill_name: str) -> Optional[str]:
        """Returns the full procedure of a specific skill."""
        skill = self.skills.get(skill_name)
        if skill:
            return f"### Skill: {skill.name}\n{skill.content}"
        return None
