# Multi-Model Orchestration with A2A + MCP

A multi-agent orchestration system that combines the **Agent-to-Agent (A2A)** protocol with **Model Context Protocol (MCP)** to enable seamless communication between AI agents and tools — all powered by **Google Gemini** via the **Google ADK**.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         CLI Client                               │
│                        (app/cli.py)                              │
│  Interactive terminal with slash commands (/skill-name)          │
└────────────────────────────┬─────────────────────────────────────┘
                             │  A2A (HTTP)
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                        Host Agent                                │
│                  (agents/host_agent, port 11000)                 │
│                                                                  │
│  • Orchestrates all communication                                │
│  • Routes requests to specialist agents OR MCP tools             │
│  • Discovers agents from utilities/a2a/agent_registry.json       │
│  • Loads MCP tools from utilities/mcp/mcp_config.json            │
│  • Executes skills from skills/ directory                        │
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
│                        │      │    port 3000 — math operations  │
└────────────────────────┘      └────────────────────────────────┘
```

### Data Flow

```
User ➜ CLI ➜ Host Agent (A2A) ──┬──➜ Website Builder Agent (A2A)
                                ├──➜ Terminal MCP Server (stdio)
                                ├──➜ Arithmetic MCP Server (HTTP)
                                └──➜ Skills (markdown workflows)
```

## Features

- **Agent Orchestration** — A host agent that discovers and delegates tasks to specialist agents
- **A2A Protocol** — Agent-to-Agent communication over HTTP for task delegation
- **MCP Integration** — Model Context Protocol for connecting to tool servers (stdio and HTTP)
- **Skills System** — Markdown-defined workflows invoked via `/slash-commands` or natural language
- **Interactive CLI** — Terminal-based chat interface with skill support
- **Extensible** — Easy to add new agents, MCP tools, and skills

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

You need **4 terminals** — run each command in order:

**Terminal 1 — MCP Arithmetic Server (port 3000):**
```bash
uv run python3 mcp_servers/servers/streamable_http_server.py
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

**More examples:**

```bash
# Use a skill with arguments
/build-landing-page dark theme portfolio site

# Natural language (skill auto-detected)
Help me calculate 25 + 17

# Direct agent interaction
build me a landing page with a hero section

# List available agents
list the agents
```

Type `:q` or `quit` to exit.

## Skills

Skills are markdown-defined workflows that can be invoked via `/slash-commands` or detected from natural language.

### Available Skills

| Skill | Description |
|-------|-------------|
| `/list-capabilities` | Lists all agents, MCP tools, and skills |
| `/build-landing-page` | Interactive landing page builder with requirements gathering |
| `/run-command` | Safe terminal command execution with explanations |
| `/quick-math` | Arithmetic calculations with step-by-step breakdown |

### Creating a New Skill

Create a markdown file in `skills/`:

```markdown
# my-skill-name

Short description for search matching.

## Instructions

Step-by-step instructions the Host Agent follows when executing this skill.
You can reference agents, MCP tools, or multi-step workflows.
```

See `skills/README.md` for full documentation.

## Project Structure

```
mcp_a2a_project/
├── app/
│   ├── __main__.py             # Entry point: `python -m app`
│   └── cli.py                  # Interactive CLI with slash commands
│
├── agents/
│   ├── host_agent/             # Orchestrator agent (port 11000)
│   │   ├── __main__.py         # Uvicorn launcher
│   │   ├── agent.py            # Core logic + skill tools
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
├── mcp_servers/
│   └── servers/
│       ├── streamable_http_server.py  # Arithmetic MCP server (port 3000)
│       └── terminal_server/           # Terminal MCP server (stdio)
│
├── skills/                      # Skill definitions
│   ├── README.md               # Skill format documentation
│   ├── list-capabilities.md    # List system capabilities
│   ├── build-landing-page.md   # Interactive page builder
│   ├── run-command.md          # Safe command execution
│   └── quick-math.md           # Arithmetic helper
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
│   ├── skills/
│   │   ├── skill_loader.py      # Parses markdown skill files
│   │   └── skill_search.py      # Search skills by name/description
│   └── common/
│       └── file_loader.py       # File reading utility
│
├── .env                         # GOOGLE_API_KEY (not committed)
├── .github/
│   └── copilot-instructions.md  # GitHub Copilot guidance
├── pyproject.toml               # Project dependencies (uv)
└── CLAUDE.md                    # AI coding assistant guidance
```

## Configuration

### Adding a New Agent

1. Create a new folder under `agents/` with these files:
   - `agent.py` — Core logic with `invoke(query, session_id)` method
   - `agent_executor.py` — A2A `AgentExecutor` bridge
   - `__main__.py` — Uvicorn launcher
   - `instructions.txt` — System prompt (required)
   - `description.txt` — Agent description (required)

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
- Use a regular command (e.g. `"uv"`) for stdio-based MCP servers

### Adding a New Skill

1. Create a markdown file in `skills/` directory
2. Follow the format: `# name`, description paragraph, `## Instructions` section
3. Skills are automatically discovered on Host Agent startup

## Key Design Patterns

| Pattern | Description |
|---------|-------------|
| **Agent structure** | Each agent has `agent.py` (core), `agent_executor.py` (A2A bridge), `__main__.py` (launcher), `instructions.txt` (prompt) |
| **Lazy initialization** | Host Agent initializes LLM + tools on first request, not at startup |
| **A2A communication** | `AgentConnector` handles HTTP task delegation between agents |
| **MCP integration** | `MCPConnect` loads tools from config and injects them into ADK agent's toolset |
| **Skills** | Markdown-defined workflows loaded by `SkillLoader`, searched by `SkillSearch` |
| **Streaming** | Responses stream via A2A protocol using `EventQueue` |

## Tech Stack

- **[Google ADK](https://github.com/google/adk-python)** — Agent Development Kit for building LLM agents
- **[Google Gemini 2.5 Flash](https://ai.google.dev/)** — LLM powering all agents
- **[A2A Protocol](https://github.com/google/A2A)** — Agent-to-Agent communication standard
- **[MCP](https://modelcontextprotocol.io/)** — Model Context Protocol for tool integration
- **[asyncclick](https://github.com/pallets-eco/click)** — Async CLI framework
- **[uv](https://docs.astral.sh/uv/)** — Fast Python package manager

## License

MIT License — see [LICENSE](LICENSE) for details.

---

> **Note:** This is an experimental project demonstrating multi-agent orchestration patterns. Use in production at your own discretion.
