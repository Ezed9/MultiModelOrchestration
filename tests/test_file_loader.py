"""
Tests for utilities/common/file_loader.py
"""

from utilities.common.file_loader import load_instructions_file


class TestLoadInstructionsFile:
    """Tests for the load_instructions_file function."""

    def test_load_existing_file(self, temp_file):
        """Should load content from an existing file."""
        expected_content = "Test instructions content"
        with open(temp_file, "w") as f:
            f.write(expected_content)
        
        result = load_instructions_file(temp_file)
        assert result == expected_content

    def test_load_nonexistent_file_returns_default(self):
        """Should return default when file doesn't exist."""
        result = load_instructions_file("/nonexistent/path/file.txt", "default_value")
        assert result == "default_value"

    def test_load_nonexistent_file_returns_empty_string_by_default(self):
        """Should return empty string when file doesn't exist and no default given."""
        result = load_instructions_file("/nonexistent/path/file.txt")
        assert result == ""

    def test_empty_filename_returns_default(self):
        """Should return default when filename is empty."""
        result = load_instructions_file("", "default")
        assert result == "default"

    def test_none_filename_returns_default(self):
        """Should return default when filename is None."""
        result = load_instructions_file(None, "default")
        assert result == "default"

    def test_load_utf8_content(self, temp_file):
        """Should handle UTF-8 encoded content."""
        expected_content = "Test with émojis 🎉 and ünïcödé"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(expected_content)
        
        result = load_instructions_file(temp_file)
        assert result == expected_content

    def test_load_empty_file(self, temp_file):
        """Should return empty string for empty file."""
        # File is created empty by fixture
        with open(temp_file, "w") as f:
            f.write("")
        
        result = load_instructions_file(temp_file)
        assert result == ""

    def test_load_multiline_content(self, temp_file):
        """Should preserve multiline content."""
        expected_content = "Line 1\nLine 2\nLine 3"
        with open(temp_file, "w") as f:
            f.write(expected_content)
        
        result = load_instructions_file(temp_file)
        assert result == expected_content
