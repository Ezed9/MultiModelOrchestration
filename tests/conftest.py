"""
Shared pytest fixtures for the MCP A2A test suite.
"""

import os
import tempfile

import pytest
from a2a.types import AgentCapabilities, AgentCard


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
def registry_file(tmp_path, sample_agent_registry):
    """Write the sample registry to disk and return its path."""
    path = tmp_path / "agent_registry.json"
    path.write_text(sample_agent_registry)
    return path


@pytest.fixture
def agent_card_factory():
    """Build valid AgentCard instances for tests."""

    def make_card(name: str, url: str = "http://localhost:9999/") -> AgentCard:
        return AgentCard(
            name=name,
            description=f"{name} description",
            url=url,
            version="1.0.0",
            default_input_modes=["text"],
            default_output_modes=["text"],
            skills=[],
            capabilities=AgentCapabilities(),
        )

    return make_card


@pytest.fixture
def sample_mcp_config():
    """Sample MCP config JSON covering both transports."""
    return """{
  "mcpServers": {
    "test_stdio_server": {
      "type": "stdio",
      "command": "echo",
      "args": ["test"]
    },
    "test_http_server": {
      "type": "streamable_http",
      "url": "http://localhost:3000/mcp/"
    }
  }
}"""
