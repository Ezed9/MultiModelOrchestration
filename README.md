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
│  mcp_servers/servers/  │       │                                  │
│                        │       │  • website_builder_simple        │
│  • terminal_server     │       │    (port 10000)                  │
│    (stdio, sandboxed)  │       │    Generates HTML/CSS/JS pages   │
│    Run shell commands  │       │                                  │
│                        │       │  • content_writer                │
│  • arithmetic_server   │       │    (port 10001)                  │
│    (HTTP, port 3000)   │       │    Copy, taglines, summaries     │
│    Math operations     │       │                                  │
└────────────────────────┘       └──────────────────────────────────┘
```

## Numbered Workflow

The diagram numbers identify the **order of system initialization and request flow**:

| Step | Component | Description |
|------|-----------|-------------|
| **① MCP Servers** | `mcp_servers/servers/` | Remote MCP tool servers start up (terminal via stdio, arithmetic via HTTP) |
| **② MCP config.json** | `utilities/mcp/mcp_config.json` | Host Agent reads this config to discover and connect to MCP servers via `MCP Connector` |
| **③ Remote A2A Agents** | `agents/website_builder_simple/`, `agents/content_writer/` | Specialist A2A agents start up with their own A2A Server + Orchestrator |
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
- **Two Specialist Agents** — website builder (HTML/CSS/JS) and content writer (copy, summaries)
- **Skills System** — Markdown-defined workflows invoked via `/slash-commands` or natural language
- **Interactive CLI** — Terminal-based chat interface with skill support
- **Extensible** — Adding an agent = a new folder + one registry line; the host discovers the rest
- **Well-Tested** — 68 unit and integration tests (discovery, routing, MCP loading, failure
  handling) that run offline in seconds, gated by GitHub Actions CI
- **One-Command Startup** — `./scripts/start.sh` boots every service in health-checked order
- **Secure** — Command whitelisting, workspace path sandboxing, and input validation for terminal
  operations

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

**One command (recommended):**

```bash
./scripts/start.sh          # start everything, Ctrl-C stops all services
./scripts/start.sh --cli    # start everything, then open the CLI
```

The script starts each service in dependency order and waits for its health
check before starting the next.

<details>
<summary><b>Or start manually</b> (5 terminals, in numbered-workflow order ① → ⑥)</summary>

**Terminal 1 — ① MCP Arithmetic Server (port 3000):**
```bash
uv run python3 mcp_servers/servers/streamable_http_server.py
```

> The terminal MCP server (stdio) is launched automatically by the Host Agent via `mcp_config.json`.

**Terminal 2 — ③ Website Builder Agent (port 10000):**
```bash
uv run python3 -m agents.website_builder_simple
```

**Terminal 3 — ③ Content Writer Agent (port 10001):**
```bash
uv run python3 -m agents.content_writer
```

**Terminal 4 — ⑤ Host Agent (port 11000):**
```bash
uv run python3 -m agents.host_agent
```

> On startup the Host Agent reads `mcp_config.json` (step ②) and `agent_registry.json` (step ④) to discover all available tools and agents, and injects the discovered agent descriptions into its system prompt.

**Terminal 5 — ⑥ CLI Client:**
```bash
uv run python3 -m app --agent http://localhost:11000 --session 0
```

</details>

### 4. Chat with the Agent

Once the CLI starts, you can use natural language or slash commands:

```
What do you want to send to the agent? (type ':q' or 'quit' to exit): /list-capabilities

[Invoking skill: list-capabilities]

Agent Response:
Here's what's available in the system:

**Agents:**
- website_builder_simple: Creates HTML/CSS/JS web pages
- content_writer: Writes marketing copy, taglines, and summaries

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
│   ├── website_builder_simple/   # ③ Remote A2A Agent (port 10000)
│   └── content_writer/           # ③ Remote A2A Agent (port 10001)
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
├── scripts/
│   └── start.sh                  # One-command startup with health checks
│
├── .github/workflows/ci.yml      # CI — ruff + pytest on every push/PR
│
├── tests/                        # 68 unit + integration tests (offline, no API key)
│
└── skills/                       # Markdown-defined workflow skills
```

## Testing

The suite has **68 unit and integration tests** that run **offline in seconds — no servers, no
API key required**. External boundaries are mocked (`httpx.MockTransport` for A2A discovery,
`AsyncMock` for the A2A client and MCP toolsets). Coverage:

| Area | Tests | What's verified |
|------|-------|-----------------|
| Agent discovery | `test_agent_discovery.py` | Registry validation, URL-scheme filtering, concurrent card fetching, per-endpoint failure isolation |
| Task routing | `test_host_agent_routing.py` | `_delegate_task` matching, case-insensitivity, unknown-agent handling, session reuse |
| A2A connector | `test_agent_connector.py` | Response extraction (status + history fallback), timeout/HTTP/protocol failure handling |
| MCP loading | `test_mcp_connect.py`, `test_mcp_discovery.py` | Both transports, config validation, one-server-down graceful degradation |
| Terminal security | `test_terminal_server.py` | Command whitelist, metacharacter blocking, workspace path sandboxing |
| Config & skills | `test_config.py`, `test_skill_loader.py`, `test_file_loader.py` | Env overrides, path helpers, markdown skill parsing |

```bash
uv run pytest        # run all tests
uv run ruff check .  # lint
```

Both run in CI on every push (`.github/workflows/ci.yml`).

## Configuration

### Environment Variables

See `.env.example` for a template.

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | (required) | Google AI API key for Gemini |
| `DEFAULT_MODEL` | `gemini-2.5-flash` | LLM model to use |
| `AGENT_DISCOVERY_TIMEOUT` | `30.0` | Timeout for agent discovery (seconds) |
| `AGENT_EXECUTION_TIMEOUT` | `300.0` | Timeout for agent execution and the CLI client (seconds) |
| `MCP_SERVER_TIMEOUT` | `5.0` | Timeout for MCP server connections (seconds) |
| `TERMINAL_COMMAND_TIMEOUT` | `30` | Timeout for terminal server commands (seconds) |
| `LOG_LEVEL` | `INFO` | Logging level for all entrypoints |
| `LOG_FORMAT` | (see `utilities/config.py`) | Log line format |
| `AGENT_REGISTRY_FILE` | `utilities/a2a/agent_registry.json` | Override the agent registry path |
| `MCP_CONFIG_FILE` | `utilities/mcp/mcp_config.json` | Override the MCP config path |

### Adding a New Agent

1. Create a new folder under `agents/` extending `BaseAgent` and `BaseAgentExecutor`
2. Register its URL in `utilities/a2a/agent_registry.json` (step ④)

### Adding a New MCP Tool Server

Edit `utilities/mcp/mcp_config.json` (step ②) with stdio or HTTP server configuration.

### Adding a New Skill

Create a markdown file in `skills/` with `# name`, description, and `## Instructions`.

## Security

- **Command Whitelisting**: Terminal server only allows specific commands (ls, cat, git, python, etc.)
- **Workspace Sandboxing**: Every path argument must resolve inside `~/mcp/workspace` — absolute
  paths and `../` escapes are rejected, so even whitelisted commands like `rm` cannot touch
  anything outside the workspace
- **Input Validation**: Shell metacharacters (`;`, `|`, `&&`, etc.) are blocked
- **Registry Validation**: Agent registry URLs are restricted to `http`/`https` schemes
- **Timeout Protection**: All commands have execution time limits
- **No Shell Expansion**: Commands run with `shell=False` to prevent injection

> **Disclosure**: early in development a `.env` file containing an API key was accidentally
> committed. The key was revoked and rotated, the file untracked, and the repository history was
> rewritten with `git-filter-repo` to purge it entirely. Secrets now live only in the untracked
> `.env` (see `.env.example`).

## Tech Stack

- **[Google ADK](https://github.com/google/adk-python)** — Agent Development Kit
- **[Google Gemini 2.5 Flash](https://ai.google.dev/)** — LLM powering all agents
- **[A2A Protocol](https://github.com/google/A2A)** — Agent-to-Agent communication
- **[MCP](https://modelcontextprotocol.io/)** — Model Context Protocol
- **[pytest](https://pytest.org/)** — Testing framework
- **[uv](https://docs.astral.sh/uv/)** — Fast Python package manager

## License

MIT License — see [LICENSE](LICENSE) for details.
