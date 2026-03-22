"""
Shared pytest fixtures for the MCP A2A test suite.
"""

import os
import tempfile
import pytest


@pytest.fixture
def temp_dir():
    """Provide a temporary directory that is cleaned up after the test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_file():
    """Provide a temporary file that is cleaned up after the test."""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def sample_skill_content():
    """Sample skill markdown content for testing."""
    return """# test-skill

This is a test skill for unit testing.

## Instructions

1. Do something
2. Do something else
3. Return the result
"""


@pytest.fixture
def sample_agent_registry():
    """Sample agent registry JSON for testing."""
    return '["http://localhost:10000", "http://localhost:11000"]'


@pytest.fixture
def sample_mcp_config():
    """Sample MCP config JSON for testing."""
    return """{
  "mcpServers": {
    "test_server": {
      "command": "echo",
      "args": ["test"]
    }
  }
}"""
