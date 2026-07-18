#!/usr/bin/env bash
# One-command startup for the whole system:
#   ./scripts/start.sh          # start all services, Ctrl-C to stop
#   ./scripts/start.sh --cli    # start all services, then open the CLI
#
# The terminal MCP server is not started here: the host agent spawns it
# over stdio as configured in utilities/mcp/mcp_config.json.
set -euo pipefail
cd "$(dirname "$0")/.."

PIDS=()
cleanup() {
    echo ""
    echo "Shutting down..."
    for pid in "${PIDS[@]}"; do
        pkill -TERM -P "$pid" 2>/dev/null || true  # uv run's python child
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait_for_url() {  # $1=url $2=name
    for _ in $(seq 1 30); do
        if curl -sf "$1" >/dev/null 2>&1; then
            echo "$2 is up"
            return 0
        fi
        sleep 1
    done
    echo "ERROR: $2 did not start" >&2
    exit 1
}

wait_for_port() {  # $1=port $2=name (MCP endpoint rejects plain GETs, so TCP check only)
    for _ in $(seq 1 30); do
        if nc -z localhost "$1" 2>/dev/null; then
            echo "$2 is up"
            return 0
        fi
        sleep 1
    done
    echo "ERROR: $2 did not start" >&2
    exit 1
}

uv run python mcp_servers/servers/streamable_http_server.py &
PIDS+=($!)
wait_for_port 3000 "arithmetic MCP server (:3000)"

uv run python -m agents.website_builder_simple &
PIDS+=($!)
uv run python -m agents.content_writer &
PIDS+=($!)
wait_for_url http://localhost:10000/.well-known/agent-card.json "website_builder_simple (:10000)"
wait_for_url http://localhost:10001/.well-known/agent-card.json "content_writer (:10001)"

uv run python -m agents.host_agent &
PIDS+=($!)
wait_for_url http://localhost:11000/.well-known/agent-card.json "host_agent (:11000)"

if [[ "${1:-}" == "--cli" ]]; then
    uv run python -m app
else
    echo ""
    echo "All services running. Connect with:"
    echo "  uv run python -m app"
    echo "Press Ctrl-C to stop everything."
    wait
fi
