# list-capabilities

Lists all available agents, MCP tools, and skills in the system. Use this to discover what the system can do.

## Instructions

When the user asks to list capabilities or wants to know what's available:

1. Call the `_list_agents` tool to get all registered agents and their descriptions.

2. List the MCP tools you have available (terminal_server for shell commands, arithmetic_server for math operations).

3. List all available skills by name and description.

4. Format the response clearly with sections:
   - **Agents**: Name and what each agent does
   - **MCP Tools**: Name and capability of each tool
   - **Skills**: Name and description of each skill

5. Offer to provide more details about any specific capability if the user is interested.
