"""
Skill loader that parses markdown skill files from the skills/ directory.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from rich.console import Console

_console = Console()


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
    """

    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self._skills: list[Skill] | None = None

    def load_skills(self) -> list[Skill]:
        """
        Load all skills from the skills directory.
        Caches the result after first load.
        """
        if self._skills is not None:
            return self._skills

        self._skills = []

        if not self.skills_dir.exists():
            _console.print(
                f"[yellow]Skills directory '{self.skills_dir}' does not exist[/yellow]"
            )
            return self._skills

        for file_path in self.skills_dir.glob("*.md"):
            # Skip README
            if file_path.name.lower() == "readme.md":
                continue

            try:
                skill = self._parse_skill_file(file_path)
                if skill:
                    self._skills.append(skill)
                    _console.print(
                        f"[green]Loaded skill: [cyan]{skill.name}[/cyan][/green]"
                    )
            except Exception as e:
                _console.print(
                    f"[red]Error loading skill from '{file_path.name}': {e}[/red]"
                )

        return self._skills

    def _parse_skill_file(self, file_path: Path) -> Skill | None:
        """
        Parse a single skill markdown file.
        
        Expected format:
        # skill-name
        
        Description paragraph.
        
        ## Instructions
        
        Instruction content...
        """
        content = file_path.read_text(encoding="utf-8")

        # Extract name from H1 heading or fallback to filename
        name_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if name_match:
            name = name_match.group(1).strip()
        else:
            name = file_path.stem  # filename without .md

        # Extract description (first paragraph after H1, before any ## heading)
        # Split content to get section before first ##
        parts = re.split(r'\n##', content, maxsplit=1)
        header_section = parts[0] if parts else content
        
        description = ""
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
        description = ' '.join(desc_lines).strip()

        # Extract instructions (content after ## Instructions)
        instr_match = re.search(
            r"##\s*Instructions\s*\n(.+?)(?=\n##|\Z)",
            content,
            re.IGNORECASE | re.DOTALL
        )
        instructions = ""
        if instr_match:
            instructions = instr_match.group(1).strip()

        if not instructions:
            _console.print(
                f"[yellow]Skill '{name}' has no ## Instructions section, skipping[/yellow]"
            )
            return None

        return Skill(
            name=name,
            description=description,
            instructions=instructions,
            file_path=str(file_path)
        )

    def reload(self) -> list[Skill]:
        """Force reload of all skills."""
        self._skills = None
        return self.load_skills()
