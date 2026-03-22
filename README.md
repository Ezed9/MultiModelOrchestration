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
- **Skills System** — Markdown-defined workflows invoked via \`/slash-commands\` or natural language
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

\`\`\`bash
git clone https://github.com/Ezed9/MultiModelOrchestration.git
cd MultiModelOrchestration

# Install all dependencies
uv sync

# Install with dev dependencies (for testing)
uv sync --extra dev
\`\`\`

### 2. Set Up Environment

Create a \`.env\` file in the project root with your Google AI API key:

\`\`\`bash
echo 'GOOGLE_API_KEY="your_api_key_here"' > .env
\`\`\`

> ⚠️ **Important:** Never commit your \`.env\` file to version control. It's already in \`.gitignore\`.

### 3. Start the Services

You need **4 terminals** — run each command in order:

**Terminal 1 — MCP Arithmetic Server (port 3000):**
\`\`\`bash
uv run python3 mcp_servers/servers/streamable_http_server.py
\`\`\`

**Terminal 2 — Website Builder Agent (port 10000):**
\`\`\`bash
uv run python3 -m agents.website_builder_simple
\`\`\`

**Terminal 3 — Host Agent (port 11000):**
\`\`\`bash
uv run python3 -m agents.host_agent
\`\`\`

**Terminal 4 — CLI Client:**
\`\`\`bash
uv run python3 -m app --agent http://localhost:11000 --session 0
\`\`\`

### 4. Chat with the Agent

Once the CLI starts, you can use natural language or slash commands:

\`\`\`
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
\`\`\`

Type \`:q\` or \`quit\` to exit.

## Testing

Run the test suite:

\`\`\`bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_terminal_server.py
\`\`\`

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| \`GOOGLE_API_KEY\` | (required) | Google AI API key for Gemini |
| \`DEFAULT_MODEL\` | \`gemini-2.5-flash\` | LLM model to use |
| \`AGENT_DISCOVERY_TIMEOUT\` | \`30.0\` | Timeout for agent discovery (seconds) |
| \`AGENT_EXECUTION_TIMEOUT\` | \`300.0\` | Timeout for agent execution (seconds) |
| \`MCP_SERVER_TIMEOUT\` | \`5.0\` | Timeout for MCP server connections (seconds) |
| \`LOG_LEVEL\` | \`INFO\` | Logging level |

### Adding a New Agent

1. Create a new folder under \`agents/\` extending \`BaseAgent\` and \`BaseAgentExecutor\`
2. Register its URL in \`utilities/a2a/agent_registry.json\`

### Adding a New MCP Tool Server

Edit \`utilities/mcp/mcp_config.json\` with stdio or HTTP server configuration.

### Adding a New Skill

Create a markdown file in \`skills/\` with \`# name\`, description, and \`## Instructions\`.

## Security

- **Command Whitelisting**: Terminal server only allows specific commands (ls, cat, git, python, etc.)
- **Input Validation**: Shell metacharacters (\`;\`, \`|\`, \`&&\`, etc.) are blocked
- **Timeout Protection**: All commands have execution time limits
- **No Shell Expansion**: Commands run with \`shell=False\` to prevent injection

## Tech Stack

- **[Google ADK](https://github.com/google/adk-python)** — Agent Development Kit
- **[Google Gemini 2.5 Flash](https://ai.google.dev/)** — LLM powering all agents
- **[A2A Protocol](https://github.com/google/A2A)** — Agent-to-Agent communication
- **[MCP](https://modelcontextprotocol.io/)** — Model Context Protocol
- **[pytest](https://pytest.org/)** — Testing framework
- **[uv](https://docs.astral.sh/uv/)** — Fast Python package manager

## License

MIT License — see [LICENSE](LICENSE) for details.
