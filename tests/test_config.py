"""
Tests for utilities/config.py
"""

import os
from unittest.mock import patch


class TestConfig:
    """Tests for configuration module."""

    def test_default_model(self):
        """Should have a default model configured."""
        from utilities.config import DEFAULT_MODEL
        assert DEFAULT_MODEL == "gemini-2.5-flash"

    def test_default_timeouts(self):
        """Should have sensible default timeout values."""
        from utilities.config import (
            AGENT_DISCOVERY_TIMEOUT,
            AGENT_EXECUTION_TIMEOUT,
            MCP_SERVER_TIMEOUT,
        )
        assert AGENT_DISCOVERY_TIMEOUT == 30.0
        assert AGENT_EXECUTION_TIMEOUT == 300.0
        assert MCP_SERVER_TIMEOUT == 5.0

    def test_env_override_model(self):
        """Should allow overriding model via environment variable."""
        with patch.dict(os.environ, {"DEFAULT_MODEL": "gpt-4"}):
            # Need to reimport to pick up new env var
            import importlib

            import utilities.config
            importlib.reload(utilities.config)
            assert utilities.config.DEFAULT_MODEL == "gpt-4"
            
            # Reset
            del os.environ["DEFAULT_MODEL"]
            importlib.reload(utilities.config)

    def test_get_agent_registry_path_default(self):
        """Should return default registry path when env not set."""
        with patch.dict(os.environ, {}, clear=False):
            if "AGENT_REGISTRY_FILE" in os.environ:
                del os.environ["AGENT_REGISTRY_FILE"]
            
            from utilities.config import get_agent_registry_path
            path = str(get_agent_registry_path())

            assert "agent_registry.json" in path
            assert "utilities/a2a" in path or "utilities\\a2a" in path

    def test_get_mcp_config_path_default(self):
        """Should return default MCP config path when env not set."""
        with patch.dict(os.environ, {}, clear=False):
            if "MCP_CONFIG_FILE" in os.environ:
                del os.environ["MCP_CONFIG_FILE"]
            
            from utilities.config import get_mcp_config_path
            path = str(get_mcp_config_path())

            assert "mcp_config.json" in path
            assert "utilities/mcp" in path or "utilities\\mcp" in path
