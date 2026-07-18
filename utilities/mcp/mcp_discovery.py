import json
from pathlib import Path
from typing import Any

from utilities.config import get_mcp_config_path


class MCPDiscovery:
    """
    Reads a JSON config file defining MCP servers and provides access
    to the server definitions under the "mcpServers" key.
    """

    def __init__(self, config_file: str | Path | None = None):
        self.config_file = Path(config_file) if config_file else get_mcp_config_path()
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        try:
            data = json.loads(self.config_file.read_text())

            if not isinstance(data, dict):
                raise ValueError(f"Invalid config format in {self.config_file}")

            return data

        except FileNotFoundError as e:
            raise FileNotFoundError(f"Config file {self.config_file} not found.") from e

        except Exception as e:
            raise RuntimeError(
                f"Error reading configuration file {self.config_file}: {e}"
            ) from e

    def list_servers(self) -> dict[str, Any]:
        """
        Returns the MCP servers defined under the "mcpServers" config key.

        Raises:
            KeyError: If "mcpServers" key is not found in the configuration.
        """
        if "mcpServers" not in self.config:
            raise KeyError(f"'mcpServers' key not found in {self.config_file}")

        return self.config.get("mcpServers", {})
