"""
MCP (Model Context Protocol) server connection and tool loading.
"""

import logging

from google.adk.tools.mcp_tool import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters

from utilities.config import MCP_SERVER_TIMEOUT
from utilities.mcp.mcp_discovery import MCPDiscovery

logger = logging.getLogger(__name__)


class MCPConnect:
    """
    Discovers MCP servers, loads their tools,
    and caches them as MCPToolsets compatible with Google ADK.
    """

    def __init__(self, config_file: str | None = None):
        """
        Initialize the MCP connector.
        
        Args:
            config_file: Optional path to MCP config file. Uses default if not provided.
        """
        self.discovery = MCPDiscovery(config_file=config_file)
        self.toolsets: list[MCPToolset] = []

    async def load_all_tools(self) -> None:
        """
        Load tools from each discovered MCP server independently.
        
        A failure on one server does not prevent loading the others,
        allowing graceful degradation when some servers are unavailable.
        """
        servers = self.discovery.list_servers()
        logger.info(f"Loading tools from {len(servers)} MCP server(s)...")
        
        for name, server in servers.items():
            try:
                toolset = self._create_toolset(name, server)
                tools = await toolset.get_tools()
                tool_names = [tool.name for tool in tools]

                logger.info(f"Loaded tools from '{name}': {', '.join(tool_names)}")
                self.toolsets.append(toolset)

            except ValueError as e:
                logger.error(f"Configuration error for server '{name}': {e}")
            except ConnectionError as e:
                logger.error(f"Connection failed for server '{name}': {e}")
            except TimeoutError as e:
                logger.error(f"Timeout connecting to server '{name}': {e}")
            except Exception as e:
                logger.error(f"Unexpected error loading tools from '{name}': {e}", exc_info=True)
    
    def _create_toolset(self, name: str, server: dict) -> MCPToolset:
        """
        Create an MCPToolset for the given server configuration.
        
        Args:
            name: Server name (for error messages)
            server: Server configuration dict
            
        Returns:
            Configured MCPToolset
            
        Raises:
            ValueError: If server configuration is invalid
        """
        command = server.get("command")
        args = server.get("args", [])
        transport_type = server.get("type", "stdio")

        if transport_type == "streamable_http":
            url = server.get("url")
            if not url:
                raise ValueError(f"Server '{name}' requires a 'url' field")
            conn = StreamableHTTPConnectionParams(url=url)
        else:
            if not command:
                raise ValueError(f"Server '{name}' is missing 'command' field")
            conn = StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=command,
                    args=args
                ),
                timeout=MCP_SERVER_TIMEOUT
            )

        return MCPToolset(connection_params=conn)

    def get_tools(self) -> list[MCPToolset]:
        """
        Get the cached list of MCPToolsets.
        
        Returns:
            Copy of the toolsets list
        """
        return self.toolsets.copy()
