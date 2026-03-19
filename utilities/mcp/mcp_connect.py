from utilities.mcp.mcp_discovery import MCPDiscovery
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from mcp import StdioServerParameters
from rich.console import Console

_console = Console()


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
        Loads tools from each discovered MCP server independently.
        A failure on one server does not prevent loading the others.
        """
        for name, server in self.discovery.list_servers().items():
            try:
                command = server.get("command")
                args = server.get("args", [])
                # Support an explicit "type" field, fall back to legacy command-as-type pattern
                transport_type = server.get("type", "")

                if transport_type == "streamable_http" or command == "streamable_http":
                    if not args:
                        raise ValueError(f"Server '{name}' has no URL in 'args'")
                    conn = StreamableHTTPConnectionParams(url=args[0])
                else:
                    if not command:
                        raise ValueError(f"Server '{name}' is missing 'command' field")
                    conn = StdioConnectionParams(
                        server_params=StdioServerParameters(
                            command=command,
                            args=args
                        ),
                        timeout=5
                    )

                toolset = MCPToolset(connection_params=conn)
                tools = await toolset.get_tools()
                tool_names = [tool.name for tool in tools]

                _console.print(
                    f"[bold green]Loaded tools from server "
                    f"[cyan]'{name}'[/cyan]: {', '.join(tool_names)}[/bold green]"
                )

                self.toolsets.append(toolset)

            except Exception as e:
                _console.print(
                    f"[bold red]Error loading tools from server '{name}' (skipping): {e}[/bold red]"
                )

    def get_tools(self) -> list[MCPToolset]:
        """
        Returns the cached list of MCPToolsets.
        """
        return self.toolsets.copy()
