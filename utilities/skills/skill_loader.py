"""
Skill loader that parses markdown skill files from the skills/ directory.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Skill:
    """Represents a parsed skill definition."""
    name: str
    description: str
    instructions: str
    file_path: str


class SkillLoader:
    """
    Loads and parses skill markdown files from a directory.
    
    Expected markdown format:
        # skill-name
        
        Description paragraph.
        
        ## Instructions
        
        Instruction content...
    """

    def __init__(self, skills_dir: str = "skills"):
        """
        Initialize the skill loader.
        
        Args:
            skills_dir: Path to the directory containing skill markdown files
        """
        self.skills_dir = Path(skills_dir)
        self._skills: list[Skill] | None = None

    def load_skills(self) -> list[Skill]:
        """
        Load all skills from the skills directory.
        
        Results are cached after first load. Use reload() to force refresh.
        
        Returns:
            List of loaded Skill objects
        """
        if self._skills is not None:
            return self._skills

        self._skills = []

        if not self.skills_dir.exists():
            logger.warning(f"Skills directory '{self.skills_dir}' does not exist")
            return self._skills

        for file_path in self.skills_dir.glob("*.md"):
            # Skip README
            if file_path.name.lower() == "readme.md":
                continue

            try:
                skill = self._parse_skill_file(file_path)
                if skill:
                    self._skills.append(skill)
                    logger.info(f"Loaded skill: {skill.name}")
            except IOError as e:
                logger.error(f"Failed to read skill file '{file_path.name}': {e}")
            except Exception as e:
                logger.error(f"Error parsing skill from '{file_path.name}': {e}", exc_info=True)

        logger.info(f"Loaded {len(self._skills)} skill(s) total")
        return self._skills

    def _parse_skill_file(self, file_path: Path) -> Skill | None:
        """
        Parse a single skill markdown file.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Skill object if parsing succeeded, None if skill is invalid
        """
        content = file_path.read_text(encoding="utf-8")

        # Extract name from H1 heading or fallback to filename
        name_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if name_match:
            name = name_match.group(1).strip()
        else:
            name = file_path.stem  # filename without .md

        # Extract description (first paragraph after H1, before any ## heading)
        description = self._extract_description(content)

        # Extract instructions (content after ## Instructions)
        instructions = self._extract_instructions(content)

        if not instructions:
            logger.warning(f"Skill '{name}' has no ## Instructions section, skipping")
            return None

        return Skill(
            name=name,
            description=description,
            instructions=instructions,
            file_path=str(file_path)
        )
    
    def _extract_description(self, content: str) -> str:
        """Extract the description paragraph from skill content."""
        # Split content to get section before first ##
        parts = re.split(r'\n##', content, maxsplit=1)
        header_section = parts[0] if parts else content
        
        # Find content after H1 line
        lines = header_section.split('\n')
        in_description = False
        desc_lines = []
        for line in lines:
            if line.startswith('# '):
                in_description = True
                continue
            if in_description:
                if line.strip():
                    desc_lines.append(line)
                elif desc_lines:  # Empty line after description = end of first paragraph
                    break
        return ' '.join(desc_lines).strip()
    
    def _extract_instructions(self, content: str) -> str:
        """Extract the instructions section from skill content."""
        instr_match = re.search(
            r"##\s*Instructions\s*\n(.+?)(?=\n##|\Z)",
            content,
            re.IGNORECASE | re.DOTALL
        )
        if instr_match:
            return instr_match.group(1).strip()
        return ""

    def reload(self) -> list[Skill]:
        """
        Force reload of all skills.
        
        Returns:
            Fresh list of loaded Skill objects
        """
        self._skills = None
        return self.load_skills()
