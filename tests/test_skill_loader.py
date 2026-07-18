"""
Tests for utilities/skills/skill_loader.py
"""

from pathlib import Path

from utilities.skills.skill_loader import SkillLoader


class TestSkillLoader:
    """Tests for the SkillLoader class."""

    def test_load_valid_skill(self, temp_dir, sample_skill_content):
        """Should load a valid skill from markdown file."""
        skill_file = Path(temp_dir) / "test-skill.md"
        skill_file.write_text(sample_skill_content)
        
        loader = SkillLoader(skills_dir=temp_dir)
        skills = loader.load_skills()
        
        assert len(skills) == 1
        assert skills[0].name == "test-skill"
        assert "test skill for unit testing" in skills[0].description
        assert "Do something" in skills[0].instructions

    def test_load_multiple_skills(self, temp_dir):
        """Should load multiple skills from directory."""
        skill1 = """# skill-one

First skill description.

## Instructions

Do task one.
"""
        skill2 = """# skill-two

Second skill description.

## Instructions

Do task two.
"""
        (Path(temp_dir) / "skill-one.md").write_text(skill1)
        (Path(temp_dir) / "skill-two.md").write_text(skill2)
        
        loader = SkillLoader(skills_dir=temp_dir)
        skills = loader.load_skills()
        
        assert len(skills) == 2
        names = [s.name for s in skills]
        assert "skill-one" in names
        assert "skill-two" in names

    def test_skip_readme(self, temp_dir, sample_skill_content):
        """Should skip README.md files."""
        (Path(temp_dir) / "README.md").write_text("# README\n\nThis is readme.")
        (Path(temp_dir) / "test-skill.md").write_text(sample_skill_content)
        
        loader = SkillLoader(skills_dir=temp_dir)
        skills = loader.load_skills()
        
        assert len(skills) == 1
        assert skills[0].name == "test-skill"

    def test_skip_skill_without_instructions(self, temp_dir):
        """Should skip skills without Instructions section."""
        invalid_skill = """# invalid-skill

This skill has no instructions section.
"""
        (Path(temp_dir) / "invalid.md").write_text(invalid_skill)
        
        loader = SkillLoader(skills_dir=temp_dir)
        skills = loader.load_skills()
        
        assert len(skills) == 0

    def test_nonexistent_directory(self):
        """Should handle nonexistent skills directory gracefully."""
        loader = SkillLoader(skills_dir="/nonexistent/path")
        skills = loader.load_skills()
        
        assert skills == []

    def test_caching(self, temp_dir, sample_skill_content):
        """Should cache results after first load."""
        (Path(temp_dir) / "test.md").write_text(sample_skill_content)
        
        loader = SkillLoader(skills_dir=temp_dir)
        skills1 = loader.load_skills()
        skills2 = loader.load_skills()
        
        assert skills1 is skills2  # Same list object

    def test_reload(self, temp_dir, sample_skill_content):
        """Should reload skills when reload() is called."""
        skill_file = Path(temp_dir) / "test.md"
        skill_file.write_text(sample_skill_content)
        
        loader = SkillLoader(skills_dir=temp_dir)
        skills1 = loader.load_skills()
        
        # Modify the skill
        skill_file.write_text(sample_skill_content.replace("test-skill", "renamed-skill"))
        
        skills2 = loader.reload()
        
        assert skills1 is not skills2
        assert skills2[0].name == "renamed-skill"

    def test_fallback_to_filename_for_name(self, temp_dir):
        """Should use filename as name if H1 is missing."""
        skill_without_h1 = """Description without H1.

## Instructions

Do something.
"""
        (Path(temp_dir) / "my-skill.md").write_text(skill_without_h1)
        
        loader = SkillLoader(skills_dir=temp_dir)
        skills = loader.load_skills()
        
        assert len(skills) == 1
        assert skills[0].name == "my-skill"
