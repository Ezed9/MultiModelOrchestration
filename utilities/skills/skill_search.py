"""
Skill search utilities for finding skills by name or description.
"""

from utilities.skills.skill_loader import Skill, SkillLoader


class SkillSearch:
    """
    Search for skills by name or description text.
    """

    def __init__(self, skill_loader: SkillLoader | None = None):
        self.loader = skill_loader or SkillLoader()
        self._skills: list[Skill] | None = None

    def _get_skills(self) -> list[Skill]:
        """Lazy load skills on first search."""
        if self._skills is None:
            self._skills = self.loader.load_skills()
        return self._skills

    def search_by_name(self, name: str) -> Skill | None:
        """
        Find a skill by exact name match (case-insensitive).
        Used for slash command lookups like /build-landing-page.
        
        Args:
            name: The skill name to find (e.g., "build-landing-page")
            
        Returns:
            The matching Skill or None if not found.
        """
        name_lower = name.lower().strip()

        for skill in self._get_skills():
            if skill.name.lower() == name_lower:
                return skill

        return None

    def search_by_text(self, query: str) -> list[Skill]:
        """
        Find skills matching a text query (case-insensitive substring match).
        Searches both name and description.
        Used for natural language intent detection.
        
        Args:
            query: The search query text
            
        Returns:
            List of matching skills, sorted by relevance:
            - Name matches first
            - Description matches second
        """
        query_lower = query.lower().strip()
        
        if not query_lower:
            return []

        name_matches: list[Skill] = []
        desc_matches: list[Skill] = []

        for skill in self._get_skills():
            # Check name match
            if query_lower in skill.name.lower():
                name_matches.append(skill)
            # Check description match (only if not already matched by name)
            elif skill.description and query_lower in skill.description.lower():
                desc_matches.append(skill)

        # Return name matches first, then description matches
        return name_matches + desc_matches

    def list_all(self) -> list[Skill]:
        """Return all available skills."""
        return self._get_skills().copy()

    def reload(self) -> None:
        """Force reload of skills from disk."""
        self._skills = None
        self.loader.reload()
