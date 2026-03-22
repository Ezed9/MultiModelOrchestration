# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-agent orchestration system combining Agent-to-Agent (A2A) protocol with Model Context Protocol (MCP). Built with Google ADK (Agent Development Kit) and Python 3.12+. Includes a skills system for markdown-defined workflows.

## Development Commands

This project uses `uv` as the package manager.

```bash
# Install dependencies
uv sync

# Start services (each in a separate terminal, in this order):
uv run python3 mcp_servers/servers/streamable_http_server.py  # MCP arithmetic server on :3000
uv run python3 -m agents.website_builder_simple               # Website builder agent on :10000
uv run python3 -m agents.host_agent                           # Host/orchestrator agent on :11000
uv run python3 -m app --agent http://localhost:11000 --session 0  # CLI client
```

## Architecture

The system has three layers:

**1. CLI Client** (`app/cli.py`) — asyncclick-based interactive CLI with slash command support (`/skill-name`).

**2. Host Agent** (`agents/host_agent/`, port 11000) — Orchestrator that:
- Routes user requests to specialist agents or MCP tools
- Discovers agents via `utilities/a2a/agent_registry.json`
- Loads MCP tools via `utilities/mcp/mcp_config.json`
- Executes skills from `skills/` directory
- Uses Google Gemini 2.5 Flash via Google ADK

**3. Specialist Agents + MCP Tools + Skills**
- **Website Builder** (`agents/website_builder_simple/`, port 10000) — generates HTML/CSS/JS
- **Terminal MCP Server** (`mcp_servers/servers/terminal_server/`) — runs shell commands via stdio
- **Arithmetic MCP Server** (`mcp_servers/servers/streamable_http_server.py`, port 3000) — HTTP-based math tools
- **Skills** (`skills/`) — markdown-defined workflows (list-capabilities, build-landing-page, run-command, quick-math)

### Data Flow

```
User → CLI → Host Agent (A2A) → delegates to → Website Builder Agent (A2A)
                              → calls → MCP tools (terminal, arithmetic)
                              → executes → Skills (markdown workflows)
```

### Key Patterns

- **Agent structure**: Each agent has `agent.py` (core logic), `agent_executor.py` (A2A `AgentExecutor` bridge), `__main__.py` (uvicorn launcher), and `instructions.txt` (system prompt).
- **Lazy initialization**: `HostAgent._init_agent()` initializes the LLM agent on first use, loading MCP tools, discovering remote agents, and loading skills.
- **A2A communication**: `AgentConnector` (`utilities/a2a/agent_connector.py`) handles HTTP-based task delegation. `AgentDiscovery` reads agent URLs from `utilities/a2a/agent_registry.json`.
- **MCP integration**: `MCPConnect` loads tools from servers defined in `utilities/mcp/mcp_config.json`. Tools become part of the ADK agent's toolset.
- **Skills**: `SkillLoader` parses markdown files from `skills/`. `SkillSearch` finds skills by name or description. Host Agent has `_list_skills()` and `_invoke_skill()` tools.
- **Streaming**: Agent responses stream via A2A protocol; executors use `EventQueue` to yield events back to callers.

### Configuration Files

- `utilities/a2a/agent_registry.json` — list of agent base URLs for discovery
- `utilities/mcp/mcp_config.json` — MCP server definitions (command/args for stdio, URL for HTTP)
- `skills/*.md` — skill definitions (name, description, instructions)
- `.env` — `GOOGLE_API_KEY` required for Gemini access
