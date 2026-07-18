"""
Tests for utilities/mcp/mcp_discovery.py — config file loading.
"""

import pytest

from utilities.mcp.mcp_discovery import MCPDiscovery


class TestMCPDiscovery:
    def test_list_servers_returns_config(self, tmp_path, sample_mcp_config):
        path = tmp_path / "mcp_config.json"
        path.write_text(sample_mcp_config)
        discovery = MCPDiscovery(config_file=path)
        servers = discovery.list_servers()
        assert set(servers) == {"test_stdio_server", "test_http_server"}
        assert servers["test_http_server"]["type"] == "streamable_http"

    def test_missing_config_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            MCPDiscovery(config_file=tmp_path / "missing.json")

    def test_invalid_json_raises_runtime_error(self, tmp_path):
        path = tmp_path / "mcp_config.json"
        path.write_text("{broken json")
        with pytest.raises(RuntimeError):
            MCPDiscovery(config_file=path)

    def test_missing_mcp_servers_key_raises_key_error(self, tmp_path):
        path = tmp_path / "mcp_config.json"
        path.write_text('{"otherKey": {}}')
        discovery = MCPDiscovery(config_file=path)
        with pytest.raises(KeyError):
            discovery.list_servers()
