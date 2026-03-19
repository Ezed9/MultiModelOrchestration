# Multi-Model Orchestration with A2A + MCP

A multi-agent orchestration system that combines the **Agent-to-Agent (A2A)** protocol with **Model Context Protocol (MCP)** to enable seamless communication between AI agents and tools — all powered by **Google Gemini** via the **Google ADK**.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         CLI Client                               │
│                        (app/cli.py)                              │
│  Interactive terminal — sends messages to the Host Agent via A2A │
└────────────────────────────┬─────────────────────────────────────┘
                             │  A2A (HTTP)
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                        Host Agent                                │
│                  (agents/host_agent, port 11000)                  │
│                                                                  │
│  • Orchestrates all communication                                │
│  • Routes requests to specialist agents OR MCP tools             │
│  • Discovers agents from utilities/a2a/agent_registry.json       │
│  • Loads MCP tools from  utilities/mcp/mcp_config.json           │
└──────────┬───────────────────────────────────┬───────────────────┘
           │  A2A (HTTP)                       │  MCP (stdio / HTTP)
           ▼                                   ▼
┌────────────────────────┐      ┌────────────────────────────────┐
│  Website Builder Agent │      │        MCP Tool Servers         │
│  (port 10000)          │      │                                │
│                        │      │  • Terminal Server (stdio)      │
│  Generates HTML, CSS,  │      │    Run shell commands           │
│  and JavaScript code   │      │                                │
│  for web pages         │      │  • Arithmetic Server (HTTP)     │
│                        │      │    port 3000 — add numbers      │
└────────────────────────┘      └────────────────────────────────┘
```

### Data Flow

```
User ➜ CLI ➜ Host Agent (A2A) ──┬──➜ Website Builder Agent (A2A)
                                ├──➜ Terminal MCP Server (stdio)
                                └──➜ Arithmetic MCP Server (HTTP)
```

## Features

- **Agent Orchestration** — A host agent that discovers and delegates tasks to specialist agents
- **A2A Protocol** — Agent-to-Agent communication over HTTP for task delegation
- **MCP Integration** — Model Context Protocol for connecting to tool servers (stdio and HTTP)
- **Interactive CLI** — Terminal-based chat interface to interact with the system
- **Extensible** — Easy to add new agents and MCP tool servers

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager
- **Google AI API key** — for Gemini model access

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/Ezed9/MultiModelOrchestration.git
cd MultiModelOrchestration

# Install all dependencies
uv sync
```

### 2. Set Up Environment

Create a `.env` file in the project root with your Google AI API key:

```bash
echo 'GOOGLE_API_KEY="your_api_key_here"' > .env
```

### 3. Start the Services

You need **3 separate terminals** for the servers, then a **4th terminal** for the CLI.

**Terminal 1 — MCP Arithmetic Server (port 3000):**
```bash
uv run mcp/servers/streamable_http_server.py
```

**Terminal 2 — Website Builder Agent (port 10000):**
```bash
uv run python3 -m agents.website_builder_simple
```

**Terminal 3 — Host Agent (port 11000):**
```bash
uv run python3 -m agents.host_agent
```

**Terminal 4 — CLI Client:**
```bash
uv run python3 -m app
```

> **Tip:** The CLI also accepts options:
> ```bash
> uv run python3 -m app --agent http://localhost:11000 --session 0
> ```

### 4. Chat with the Agent

Once the CLI starts, you'll see a prompt. Try these:

```
What do you want to send to the agent? (type ':q' or 'quit' to exit): what can you do

Agent Response:
I can help you with the following:
- List and delegate to other agents
- Execute terminal commands via terminal_server
- Perform arithmetic via add_numbers
- Build websites by delegating to the website_builder_simple agent

What do you want to send to the agent? (type ':q' or 'quit' to exit): list the agents

Agent Response:
The following agents are available:
* website_builder_simple: A simple website builder that can create basic web pages

What do you want to send to the agent? (type ':q' or 'quit' to exit): build me a landing page with a dark theme

Agent Response:
(returns full HTML/CSS/JS code)

What do you want to send to the agent? (type ':q' or 'quit' to exit): quit
```

Type `:q` or `quit` to exit the CLI.

## Project Structure

```
mcp_a2a_project/
├── app/
│   ├── __main__.py             # Entry point: `python -m app`
│   └── cli.py                  # Interactive CLI (asyncclick)
│
├── agents/
│   ├── host_agent/             # Orchestrator agent (port 11000)
│   │   ├── __main__.py         # Uvicorn launcher
│   │   ├── agent.py            # Core agent logic (Google ADK LlmAgent)
│   │   ├── agent_executor.py   # A2A AgentExecutor bridge
│   │   ├── instructions.txt    # System prompt
│   │   └── description.txt     # Agent description
│   │
│   └── website_builder_simple/ # Website builder agent (port 10000)
│       ├── __main__.py         # Uvicorn launcher
│       ├── agent.py            # Core agent logic
│       ├── agent_executor.py   # A2A AgentExecutor bridge
│       ├── instructions.txt    # System prompt
│       └── description.txt     # Agent description
│
├── mcp/
│   └── servers/
│       ├── streamable_http_server.py  # Arithmetic MCP server (port 3000)
│       └── terminal_server/           # Terminal MCP server (stdio)
│
├── utilities/
│   ├── a2a/
│   │   ├── agent_connector.py   # Sends tasks to remote A2A agents
│   │   ├── agent_discovery.py   # Discovers agents from registry
│   │   └── agent_registry.json  # List of agent URLs
│   ├── mcp/
│   │   ├── mcp_connect.py       # Loads MCP tools into ADK agent
│   │   ├── mcp_discovery.py     # Reads MCP server config
│   │   └── mcp_config.json      # MCP server definitions
│   └── common/
│       └── file_loader.py       # File reading utility
│
├── .env                         # GOOGLE_API_KEY (not committed)
├── pyproject.toml               # Project dependencies (uv)
└── CLAUDE.md                    # AI coding assistant guidance
```

## Configuration

### Adding a New Agent

1. Create a new folder under `agents/` with `agent.py`, `agent_executor.py`, `__main__.py`, `instructions.txt`, and `description.txt`
2. Register its URL in `utilities/a2a/agent_registry.json`:

```json
[
    "http://localhost:10000",
    "http://localhost:12000"
]
```

### Adding a New MCP Tool Server

Edit `utilities/mcp/mcp_config.json`:

```json
{
  "mcpServers": {
    "my_new_server": {
      "command": "uv",
      "args": ["--directory", "mcp/servers/my_server", "run", "server.py"]
    },
    "my_http_server": {
      "command": "streamable_http",
      "args": ["http://localhost:4000/mcp/"]
    }
  }
}
```

- Use `"command": "streamable_http"` for HTTP-based MCP servers
- Use a regular command (e.g. `"uv"`) for stdio-based MCP servers

### Key Design Patterns

| Pattern | Description |
|---|---|
| **Agent structure** | Each agent has `agent.py` (core), `agent_executor.py` (A2A bridge), `__main__.py` (launcher), `instructions.txt` (prompt) |
| **Lazy init** | Host agent initializes LLM + tools on first request, not at startup |
| **A2A communication** | `AgentConnector` handles HTTP task delegation between agents |
| **MCP integration** | `MCPConnect` loads tools from config and injects them into the ADK agent's toolset |
| **Streaming** | Responses stream via A2A protocol using `EventQueue` |

## Tech Stack

- **[Google ADK](https://github.com/google/adk)** — Agent Development Kit for building LLM agents
- **[Google Gemini 2.5 Flash](https://ai.google.dev/)** — LLM powering all agents
- **[A2A Protocol](https://github.com/google/a2a)** — Agent-to-Agent communication standard
- **[MCP](https://modelcontextprotocol.io/)** — Model Context Protocol for tool integration
- **[asyncclick](https://github.com/pallets-eco/click)** — Async CLI framework
- **[uv](https://docs.astral.sh/uv/)** — Fast Python package manager

## License

MIT License — see [LICENSE](LICENSE) for details.

---

> **Note:** This is an experimental project demonstrating multi-agent orchestration patterns. Use in production at your own discretion.
