import os
import json
from typing import Dict, Any

class MCPDiscovery:
    """
    Reads a JSON config file defining MCP servers
    and provides access to the server definitions
    under the "mcpServers" key.

    Attributes:
        config_file (str): Path to the JSON config file.
        config (Dict[str, Any]): Parsed JSON content expected
                                 to contain the "mcpServers" key.
    """

    def __init__(self, config_file: str = None):
        """
        Initializes the MCPDiscovery with a config file.

        Args:
            config_file (str, optional): Path to the JSON config file.
                                         If None, defaults to 'mcp_config.json'
                                         located in the same directory.
        """
        if config_file is None:
            self.config_file = os.path.join(
                os.path.dirname(__file__),
                "mcp_config.json"
            )
        else:
            self.config_file = config_file

        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Loads and parses the configuration file.

        Returns:
            Dict[str, Any]: Parsed JSON content.

        Raises:
            ValueError: If JSON is not a dictionary.
            FileNotFoundError: If config file doesn't exist.
            RuntimeError: For any other read/parse errors.
        """
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)

                if not isinstance(data, dict):
                    raise ValueError(f"Invalid config format in {self.config_file}")

                return data

        except FileNotFoundError:
            raise FileNotFoundError(f"Config file {self.config_file} not found.")

        except Exception as e:
            raise RuntimeError(f"Error reading configuration file {self.config_file}: {e}")

    def list_servers(self) -> Dict[str, Any]:
        """
        Returns the MCP servers defined in the configuration file.

        Returns:
            Dict[str, Any]: The content of the "mcpServers" key from the config.

        Raises:
            KeyError: If "mcpServers" key is not found in the configuration.
        """
        if "mcpServers" not in self.config:
            raise KeyError(f"'mcpServers' key not found in {self.config_file}")

        return self.config.get("mcpServers", {})