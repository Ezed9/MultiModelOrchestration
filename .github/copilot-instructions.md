# Copilot Instructions

Multi-agent orchestration system combining A2A (Agent-to-Agent) protocol with MCP (Model Context Protocol), built with Google ADK and Python 3.12+.

## Development Commands

```bash
# Install dependencies
uv sync

# Start services (each in a separate terminal, in this order):
uv run python3 -m mcp_servers.servers.streamable_http_server     # MCP arithmetic server on :3000
uv run python3 -m agents.website_builder_simple          # Website builder agent on :10000
uv run python3 -m agents.host_agent                      # Host/orchestrator agent on :11000
uv run python3 -m app --agent http://localhost:11000 --session 0  # CLI client
```

## Architecture

Three-layer system:

```
User → CLI → Host Agent (A2A) → delegates to → Specialist Agents (A2A)
                              → calls → MCP Tools (stdio/HTTP)
```

**Host Agent** (port 11000) orchestrates everything:
- Discovers agents from `utilities/a2a/agent_registry.json`
- Loads MCP tools from `utilities/mcp/mcp_config.json`
- Delegates tasks to specialist agents or invokes MCP tools
- Uses Google Gemini 2.5 Flash via Google ADK

**Specialist Agents** (e.g., Website Builder on port 10000):
- Standalone agents with specific capabilities
- Communicate with Host Agent via A2A protocol

**MCP Tools**:
- Terminal Server (stdio) — shell commands
- Arithmetic Server (HTTP on port 3000) — math operations

## Agent Structure Convention

Every agent follows this structure:
```
agents/<agent_name>/
├── agent.py           # Core logic: LlmAgent + invoke() method
├── agent_executor.py  # A2A bridge: AgentExecutor subclass
├── __main__.py        # Uvicorn launcher
├── instructions.txt   # System prompt (required, loaded at init)
└── description.txt    # Agent description (required, loaded at init)
```

Key patterns:
- `agent.py` creates an `LlmAgent` with `model="gemini-2.5-flash"`
- `invoke(query, session_id)` returns `AsyncGenerator[dict, None]` yielding `{is_task_complete, content/updates}`
- Host Agent uses lazy initialization via `_init_agent()` with async lock
- Both `instructions.txt` and `description.txt` are required — agents raise `RuntimeError` if missing

## Configuration Files

**`utilities/a2a/agent_registry.json`** — Register agent URLs for discovery:
```json
["http://localhost:10000", "http://localhost:12000"]
```

**`utilities/mcp/mcp_config.json`** — Define MCP servers:
```json
{
  "mcpServers": {
    "my_stdio_server": {
      "command": "uv",
      "args": ["--directory", "mcp_servers/servers/my_server", "run", "server.py"]
    },
    "my_http_server": {
      "command": "streamable_http",
      "args": ["http://localhost:4000/mcp/"]
    }
  }
}
```
- Use `"command": "streamable_http"` for HTTP-based MCP servers
- Use regular commands (e.g., `"uv"`) for stdio-based servers

## Environment Setup

Requires `.env` file in project root:
```bash
GOOGLE_API_KEY="your_api_key_here"
```

## Adding New Components

**New Agent:**
1. Create folder under `agents/` with the five required files
2. Register URL in `utilities/a2a/agent_registry.json`
3. Follow the invoke pattern: yield `{is_task_complete: False, updates: str}` while working, then `{is_task_complete: True, content: str}` when done

**New MCP Server:**
1. Add server code under `mcp_servers/servers/`
2. Register in `utilities/mcp/mcp_config.json`

**New Skill:**
1. Create markdown file in `skills/` directory
2. Format:
   ```markdown
   # skill-name
   
   Short description for search matching.
   
   ## Instructions
   
   Step-by-step instructions the Host Agent follows.
   ```
3. Skills can be invoked via `/skill-name` in CLI or detected by Host Agent from natural language
