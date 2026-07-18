"""
Centralized configuration for the MCP A2A project.

All configurable values should be defined here and imported elsewhere.
Values can be overridden via environment variables.
"""

import logging
import os
from pathlib import Path
from typing import Final

# ---------------------------------------------------------------------------
# Model Configuration
# ---------------------------------------------------------------------------
DEFAULT_MODEL: Final[str] = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")

# ---------------------------------------------------------------------------
# Timeout Configuration (in seconds)
# ---------------------------------------------------------------------------
AGENT_DISCOVERY_TIMEOUT: Final[float] = float(
    os.getenv("AGENT_DISCOVERY_TIMEOUT", "30.0")
)
AGENT_EXECUTION_TIMEOUT: Final[float] = float(
    os.getenv("AGENT_EXECUTION_TIMEOUT", "300.0")
)
MCP_SERVER_TIMEOUT: Final[float] = float(
    os.getenv("MCP_SERVER_TIMEOUT", "5.0")
)

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: Final[str] = os.getenv(
    "LOG_FORMAT",
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def configure_logging() -> None:
    """Configure root logging for an application entrypoint."""
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)


# ---------------------------------------------------------------------------
# Path Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent


def get_agent_registry_path() -> Path:
    """Get the path to the agent registry file."""
    env_path = os.getenv("AGENT_REGISTRY_FILE")
    if env_path:
        return Path(env_path)
    return PROJECT_ROOT / "utilities" / "a2a" / "agent_registry.json"


def get_mcp_config_path() -> Path:
    """Get the path to the MCP config file."""
    env_path = os.getenv("MCP_CONFIG_FILE")
    if env_path:
        return Path(env_path)
    return PROJECT_ROOT / "utilities" / "mcp" / "mcp_config.json"
