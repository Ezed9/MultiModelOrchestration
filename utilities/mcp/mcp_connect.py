from utilities.mcp.mcp_discovery import MCPDiscovery
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from mcp import StdioServerParameters


class MCPConnect:
    """
    Discovers MCP servers, loads their tools,
    and caches them as MCPToolsets compatible with Google ADK.
    """

    def __init__(self, config_file: str = None):
        self.discovery = MCPDiscovery(config_file=config_file)
        self.toolsets: list[MCPToolset] = []

    async def load_all_tools(self):
        """
        Loads all tools from discovered MCP servers
        and caches them as MCPToolsets.
        """
        try:
            for name, server in self.discovery.list_servers():
                # Choose connection type
                if server.get("command") == "streamable_http":
                    conn = StreamableHTTPConnectionParams(
                        url=server["args"][0]
                    )
                else:
                    conn = StdioConnectionParams(
                        server_params=StdioServerParameters(
                            command=server["command"],
                            args=server["args"]
                        ),
                        timeout=5
                    )

                toolset = MCPToolset(connection_params=conn)

                # Fetch tools from server
                tools = await toolset.get_tools()
                tool_names = [tool.name for tool in tools]

                print(
                    f"[bold green]Loaded tools from server "
                    f"[cyan]'{name}'[/cyan]: {', '.join(tool_names)}[/bold green]"
                )

                # Cache toolset
                self.toolsets.append(toolset)

        except Exception as e:
            print(
                f"[bold red]Error loading tools from server "
                f"(skipping) '{name}': {e}[/bold red]"
            )

    def get_tools(self) -> list[MCPToolset]:
        """
        Returns the cached list of MCPToolsets.
        """
        return self.toolsets.copy()