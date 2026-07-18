"""
Tests for utilities/mcp/mcp_connect.py — toolset creation and failure isolation.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from google.adk.tools.mcp_tool import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

from utilities.config import MCP_SERVER_TIMEOUT
from utilities.mcp.mcp_connect import MCPConnect


@pytest.fixture
def config_path(tmp_path, sample_mcp_config):
    path = tmp_path / "mcp_config.json"
    path.write_text(sample_mcp_config)
    return path


class FakeToolset:
    """Stands in for MCPToolset; records params and serves fake tools."""

    def __init__(self, connection_params):
        self.connection_params = connection_params
        self.get_tools = AsyncMock(
            return_value=[SimpleNamespace(name="tool_a"), SimpleNamespace(name="tool_b")]
        )


class TestCreateToolset:
    def test_create_toolset_stdio_params(self, config_path, monkeypatch):
        monkeypatch.setattr("utilities.mcp.mcp_connect.MCPToolset", FakeToolset)
        connector = MCPConnect(config_file=config_path)
        toolset = connector._create_toolset(
            "stdio_server", {"type": "stdio", "command": "echo", "args": ["hi"]}
        )
        params = toolset.connection_params
        assert isinstance(params, StdioConnectionParams)
        assert params.server_params.command == "echo"
        assert params.server_params.args == ["hi"]
        assert params.timeout == MCP_SERVER_TIMEOUT

    def test_create_toolset_streamable_http_params(self, config_path, monkeypatch):
        monkeypatch.setattr("utilities.mcp.mcp_connect.MCPToolset", FakeToolset)
        connector = MCPConnect(config_file=config_path)
        toolset = connector._create_toolset(
            "http_server",
            {"type": "streamable_http", "url": "http://localhost:3000/mcp/"},
        )
        params = toolset.connection_params
        assert isinstance(params, StreamableHTTPConnectionParams)
        assert params.url == "http://localhost:3000/mcp/"

    def test_create_toolset_http_missing_url_raises(self, config_path):
        connector = MCPConnect(config_file=config_path)
        with pytest.raises(ValueError, match="requires a 'url'"):
            connector._create_toolset("bad_http", {"type": "streamable_http"})

    def test_create_toolset_stdio_missing_command_raises(self, config_path):
        connector = MCPConnect(config_file=config_path)
        with pytest.raises(ValueError, match="missing 'command'"):
            connector._create_toolset("bad_stdio", {"type": "stdio", "args": []})


class TestLoadAllTools:
    async def test_load_all_tools_loads_every_server(self, config_path, monkeypatch):
        monkeypatch.setattr("utilities.mcp.mcp_connect.MCPToolset", FakeToolset)
        connector = MCPConnect(config_file=config_path)
        await connector.load_all_tools()
        assert len(connector.get_tools()) == 2

    async def test_load_all_tools_isolates_per_server_failure(
        self, config_path, monkeypatch
    ):
        created = []

        class FlakyToolset(FakeToolset):
            def __init__(self, connection_params):
                super().__init__(connection_params)
                if not created:  # first server fails, second succeeds
                    self.get_tools = AsyncMock(side_effect=RuntimeError("server down"))
                created.append(self)

        monkeypatch.setattr("utilities.mcp.mcp_connect.MCPToolset", FlakyToolset)
        connector = MCPConnect(config_file=config_path)
        await connector.load_all_tools()

        assert len(created) == 2  # both servers were attempted
        assert len(connector.get_tools()) == 1  # only the healthy one is cached
