# Multi-Model Orchestration with A2A and MCP

A sophisticated multi-agent orchestration system that combines Agent-to-Agent (A2A) protocol with Model Context Protocol (MCP) to enable seamless communication between AI agents and tools.

## 🌟 Features

- **Agent Orchestration**: Host agent that coordinates multiple specialized agents
- **A2A Protocol**: Agent-to-Agent communication for task delegation
- **MCP Integration**: Model Context Protocol for tool connectivity
- **CLI Interface**: Interactive command-line interface for agent interaction
- **Extensible Architecture**: Easy to add new agents and tools

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Client                            │
│                    (app/cmd/cmd.py)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Host Agent                              │
│                 (agents/host_agent)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  • Orchestrates agent communication                   │  │
│  │  • Routes requests to appropriate agents/tools        │  │
│  │  • Manages MCP tool integration                       │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────┬─────────────────────────────┬──────────────────┘
            │                             │
            ▼                             ▼
┌───────────────────────┐    ┌──────────────────────────────┐
│  Website Builder      │    │     MCP Tools                │
│  Agent                │    │  • Terminal Server           │
│  (port 10000)         │    │  • Arithmetic Server         │
└───────────────────────┘    └──────────────────────────────┘
```

## 📋 Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Google AI API key

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Ezed9/MultiModelOrchestration.git
cd MultiModelOrchestration
```

### 2. Set Up Environment

Create a `.env` file with your Google AI API key:

```bash
echo 'GOOGLE_API_KEY="your_api_key_here"' > .env
```

### 3. Install Dependencies

```bash
uv sync
```

### 4. Start the MCP Servers

In separate terminals:

```bash
# Terminal 1: Start MCP HTTP server
uv run mcp/servers/streamable_http_server.py

# Terminal 2: Start website builder agent
uv run python3 -m agents.website_builder_simple

# Terminal 3: Start host agent
uv run python3 -m agents.host_agent
```

### 5. Run the CLI

```bash
uv run python3 -m app.cmd.cmd
```

## 💬 Usage Examples

Once the CLI is running, you can interact with the host agent:

```
What do you want to send to the agent? (type ':q' or 'quit' to exit): what can you do

Agent Response:
I can help you with the following:
- List and delegate to other agents
- Execute terminal commands via terminal_server
- Perform arithmetic via add_numbers

What do you want to send to the agent? (type ':q' or 'quit' to exit): list the agents

Agent Response:
The following agents are available:
* website_builder_simple: A simple website builder that can create basic web pages
```

## 🛠️ Project Structure

```
mcp_a2a_project/
├── agents/
│   ├── host_agent/          # Main orchestrator agent
│   │   ├── agent.py
│   │   ├── instructions.txt
│   │   └── description.txt
│   └── website_builder_simple/  # Website builder agent
│       ├── agent.py
│       └── ...
├── app/
│   └── cmd/
│       └── cmd.py           # CLI interface
├── utilities/
│   ├── a2a/                 # A2A protocol utilities
│   │   ├── agent_connector.py
│   │   ├── agent_discovery.py
│   │   └── agent_registry.json
│   ├── mcp/                 # MCP utilities
│   │   ├── mcp_connect.py
│   │   ├── mcp_discovery.py
│   │   └── mcp_servers.json
│   └── common/
│       └── file_loader.py
└── mcp/
    └── servers/             # MCP server implementations
        ├── streamable_http_server.py
        └── ...
```

## 🔧 Configuration

### MCP Servers Configuration

Edit `utilities/mcp/mcp_servers.json` to add or modify MCP servers:

```json
{
  "terminal_server": {
    "command": "uvx",
    "args": ["mcp-server-commands"]
  },
  "arithmetic_server": {
    "command": "streamable_http",
    "args": ["http://localhost:8000"]
  }
}
```

### Agent Registry

Edit `utilities/a2a/agent_registry.json` to register agents:

```json
[
  "http://localhost:10000"
]
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Google ADK](https://github.com/google/adk)
- Uses [A2A Protocol](https://github.com/google/a2a) for agent communication
- Integrates [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Note**: This is an experimental project demonstrating multi-agent orchestration patterns. Use in production environments at your own discretion.
