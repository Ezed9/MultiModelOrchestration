# Multi-Model Orchestration with A2A + MCP

A multi-agent orchestration system that combines the **Agent-to-Agent (A2A)** protocol with **Model Context Protocol (MCP)** to enable seamless communication between AI agents and tools — all powered by **Google Gemini** via the **Google ADK**.

## Architecture

The system is divided into **three zones**, connected by A2A and MCP protocols:

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                        Multi-agent MCP + A2A System                            ║
╠══════════════════╦═══════════════════════════════════╦══════════════════════════╣
║  1. A2A/MCP      ║  2. A2A/MCP Multi-agent System   ║  3. Remote A2A Agents   ║
║     Frontend     ║                                   ║     & MCP Servers       ║
╚══════════════════╩═══════════════════════════════════╩══════════════════════════╝
```

### Zone 1 — A2A/MCP Frontend (`app/`)

```
┌───────────────────────┐
│      User Input       │   ← Natural language / slash commands
└──────────┬────────────┘
           │
┌──────────▼────────────┐
│     App Frontend      │   app/cli.py
│  ┌────────────────┐   │
│  │   A2A Client   │   │   Sends tasks over A2A (HTTP) to the Host Agent
│  └────────────────┘   │
└──────────┬────────────┘
           │  A2A (HTTP)
```

### Zone 2 — A2A/MCP Multi-agent System (`agents/host_agent/`)

```
           │  A2A (HTTP)
           ▼
┌──────────────────────────────────────────────────────────────────┐
│                      A2A Server + Host Agent                     │
│                    agents/host_agent/  (port 11000)              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                      Orchestrator                        │    │
│  │                                                         │    │
│  │  ┌────────────────────────┐  ┌──────────────────────┐  │    │
│  │  │     MCP Connector      │  │   Agent Connector n  │  │    │
│  │  │  utilities/mcp/        │  │  utilities/a2a/       │  │    │
│  │  │  • mcp_connect.py      │  │  • agent_connector.py│  │    │
│  │  │  • mcp_discovery.py    │  │  • agent_discovery.py│  │    │
│  │  └──────────┬─────────────┘  └──────────┬───────────┘  │    │
│  │             │                            │              │    │
│  │  ┌──────────▼──────────┐   ┌────────────▼───────────┐  │    │
│  │  │   MCP config.json   │   │     Agent Registry     │  │    │
│  │  │  List Servers ②    │   │     List Agents   ④    │  │    │
│  │  └─────────────────────┘   └────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────┬──────────────────────────────────────┬───────────────┘
           │  MCP (stdio / HTTP)                  │  A2A (HTTP)
```

### Zone 3 — Remote MCP Servers & A2A Agents

```
           │  MCP                                 │  A2A
           ▼                                      ▼
┌────────────────────────┐       ┌──────────────────────────────────┐
│      MCP Servers  ①   │       │         A2A Agents  ③            │
│  mcp_servers/servers/  │       │  agents/website_builder_simple/  │
│                        │       │  (port 10000)                    │
│  • terminal_server     │       │                                  │
│    (stdio)             │       │  ┌────────────────────────────┐  │
│    Run shell commands  │       │  │  A2A Server + Orchestrator  │  │
│                        │       │  │  Remote Agent n            │  │
│  • arithmetic_server   │       │  └────────────────────────────┘  │
│    (HTTP, port 3000)   │       │                                  │
│    Math operations     │       │  Generates HTML/CSS/JS pages     │
└────────────────────────┘       └──────────────────────────────────┘
```

## Numbered Workflow

The diagram numbers identify the **order of system initialization and request flow**:

| Step | Component | Description |
|------|-----------|-------------|
| **① MCP Servers** | `mcp_servers/servers/` | Remote MCP tool servers start up (terminal via stdio, arithmetic via HTTP) |
| **② MCP config.json** | `utilities/mcp/mcp_config.json` | Host Agent reads this config to discover and connect to MCP servers via `MCP Connector` |
| **③ Remote A2A Agents** | `agents/website_builder_simple/` | Specialist A2A agents start up with their own A2A Server + Orchestrator |
| **④ Agent Registry** | `utilities/a2a/agent_registry.json` | Host Agent reads this registry to discover remote A2A agents via `Agent Connector` |
| **⑤ Host Agent** | `agents/host_agent/` (port 11000) | Central orchestrator — routes tasks to MCP tools or A2A agents based on intent |
| **⑥ App Frontend** | `app/cli.py` | User-facing CLI with A2A Client that sends requests to the Host Agent |

### End-to-End Request Flow

```
User Input
    │
    ▼
App Frontend (A2A Client)  ──A2A──►  Host Agent / Orchestrator
                                              │
                          ┌───────────────────┼──────────────────────┐
                          │                   │                      │
                          ▼                   ▼                      ▼
                    MCP Connector       Agent Connector         Skills System
                          │                   │               (markdown files)
                    ┌─────▼──────┐    ┌───────▼──────────┐
                    │ MCP Servers│    │ Remote A2A Agents │
                    │ (①)        │    │ (③)               │
                    └────────────┘    └──────────────────┘
```

## Features

- **Agent Orchestration** — A host agent that discovers and delegates tasks to specialist agents
- **A2A Protocol** — Agent-to-Agent communication over HTTP for task delegation
- **MCP Integration** — Model Context Protocol for connecting to tool servers (stdio and HTTP)
- **Skills System** — Markdown-defined workflows invoked via `/slash-commands` or natural language
- **Interactive CLI** — Terminal-based chat interface with skill support
- **Extensible** — Easy to add new agents, MCP tools, and skills
- **Well-Tested** — Comprehensive test suite with 32+ unit tests
- **Secure** — Command whitelisting and input validation for terminal operations

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

# Install with dev dependencies (for testing)
uv sync --extra dev
```

### 2. Set Up Environment

Create a `.env` file in the project root with your Google AI API key:

```bash
echo 'GOOGLE_API_KEY="your_api_key_here"' > .env
```

> ⚠️ **Important:** Never commit your `.env` file to version control. It's already in `.gitignore`.

### 3. Start the Services

Start components in order, following the numbered workflow (① → ⑥). You need **4 terminals**:

**Terminal 1 — ① MCP Arithmetic Server (port 3000):**
```bash
uv run python3 mcp_servers/servers/streamable_http_server.py
```

> The terminal MCP server (stdio) is launched automatically by the Host Agent via `mcp_config.json`.

**Terminal 2 — ③ Website Builder Agent (port 10000):**
```bash
uv run python3 -m agents.website_builder_simple
```

**Terminal 3 — ⑤ Host Agent (port 11000):**
```bash
uv run python3 -m agents.host_agent
```

> On startup the Host Agent reads `mcp_config.json` (step ②) and `agent_registry.json` (step ④) to discover all available tools and agents.

**Terminal 4 — ⑥ CLI Client:**
```bash
uv run python3 -m app --agent http://localhost:11000 --session 0
```

### 4. Chat with the Agent

Once the CLI starts, you can use natural language or slash commands:

```
What do you want to send to the agent? (type ':q' or 'quit' to exit): /list-capabilities

[Invoking skill: list-capabilities]

Agent Response:
Here's what's available in the system:

**Agents:**
- website_builder_simple: Creates HTML/CSS/JS web pages

**MCP Tools:**
- terminal_server: Execute shell commands
- add_numbers: Perform arithmetic

**Skills:**
- /list-capabilities: Lists all available capabilities
- /build-landing-page: Interactive landing page builder
- /run-command: Safe terminal command execution
- /quick-math: Arithmetic with explanations
```

Type `:q` or `quit` to exit.

## Project Structure

```
mcp_a2a_project/
├── app/                          # ⑥ Frontend — CLI client (A2A Client)
│   ├── cli.py
│   └── __main__.py
│
├── agents/
│   ├── host_agent/               # ⑤ Host Agent — central orchestrator (port 11000)
│   │   ├── agent.py
│   │   ├── agent_executor.py
│   │   └── __main__.py
│   └── website_builder_simple/   # ③ Remote A2A Agent (port 10000)
│
├── mcp_servers/
│   └── servers/                  # ① MCP Tool Servers
│       ├── terminal_server/      #   stdio — shell command execution
│       └── streamable_http_server.py  # HTTP, port 3000 — arithmetic
│
├── utilities/
│   ├── a2a/
│   │   ├── agent_registry.json   # ④ Agent Registry — list of remote A2A agents
│   │   ├── agent_connector.py    #   A2A client for delegating tasks
│   │   └── agent_discovery.py    #   Fetches agent cards from remote agents
│   └── mcp/
│       ├── mcp_config.json       # ② MCP Config — list of MCP servers
│       ├── mcp_connect.py        #   MCP Client connector
│       └── mcp_discovery.py      #   Discovers tools from MCP servers
│
└── skills/                       # Markdown-defined workflow skills
```

## Testing

Run the test suite:

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_terminal_server.py
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | (required) | Google AI API key for Gemini |
| `DEFAULT_MODEL` | `gemini-2.5-flash` | LLM model to use |
| `AGENT_DISCOVERY_TIMEOUT` | `30.0` | Timeout for agent discovery (seconds) |
| `AGENT_EXECUTION_TIMEOUT` | `300.0` | Timeout for agent execution (seconds) |
| `MCP_SERVER_TIMEOUT` | `5.0` | Timeout for MCP server connections (seconds) |
| `LOG_LEVEL` | `INFO` | Logging level |

### Adding a New Agent

1. Create a new folder under `agents/` extending `BaseAgent` and `BaseAgentExecutor`
2. Register its URL in `utilities/a2a/agent_registry.json` (step ④)

### Adding a New MCP Tool Server

Edit `utilities/mcp/mcp_config.json` (step ②) with stdio or HTTP server configuration.

### Adding a New Skill

Create a markdown file in `skills/` with `# name`, description, and `## Instructions`.

## Security

- **Command Whitelisting**: Terminal server only allows specific commands (ls, cat, git, python, etc.)
- **Input Validation**: Shell metacharacters (`;`, `|`, `&&`, etc.) are blocked
- **Timeout Protection**: All commands have execution time limits
- **No Shell Expansion**: Commands run with `shell=False` to prevent injection

## Tech Stack

- **[Google ADK](https://github.com/google/adk-python)** — Agent Development Kit
- **[Google Gemini 2.5 Flash](https://ai.google.dev/)** — LLM powering all agents
- **[A2A Protocol](https://github.com/google/A2A)** — Agent-to-Agent communication
- **[MCP](https://modelcontextprotocol.io/)** — Model Context Protocol
- **[pytest](https://pytest.org/)** — Testing framework
- **[uv](https://docs.astral.sh/uv/)** — Fast Python package manager

## License

MIT License — see [LICENSE](LICENSE) for details.
