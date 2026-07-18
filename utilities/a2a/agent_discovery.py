import asyncio
import json
import logging
from pathlib import Path
from urllib.parse import urlparse

import httpx
from a2a.client import A2ACardResolver
from a2a.types import AgentCard

from utilities.config import AGENT_DISCOVERY_TIMEOUT, get_agent_registry_path

logger = logging.getLogger(__name__)

_ALLOWED_URL_SCHEMES = {"http", "https"}


class AgentDiscovery:
    """
    Discovers A2A Agents by reading a registry file of URLs and
    querying each one's agent-card endpoint to retrieve an AgentCard.
    """

    def __init__(self, registry_file: str | Path | None = None):
        self.registry_file = Path(registry_file) if registry_file else get_agent_registry_path()
        self.base_urls = self._load_registry()

    def _load_registry(self) -> list[str]:
        """
        Load and validate agent URLs from the registry JSON file.
        """
        try:
            data = json.loads(self.registry_file.read_text())

            if not isinstance(data, list):
                raise ValueError("Registry file must contain a list of URLs")

            validated = []
            for entry in data:
                if not isinstance(entry, str):
                    logger.warning("Registry entry is not a string (skipping): %r", entry)
                    continue
                scheme = urlparse(entry).scheme
                if scheme not in _ALLOWED_URL_SCHEMES:
                    logger.warning(
                        "Registry URL has disallowed scheme '%s' (skipping): %s",
                        scheme, entry
                    )
                    continue
                validated.append(entry)

            return validated

        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Agent registry file not found: {self.registry_file}. "
                "Check that the file exists and the path is correct."
            ) from e

        except json.JSONDecodeError:
            logger.error("Registry file contains invalid JSON: %s", self.registry_file)
            return []

        except Exception as e:
            logger.error("Error loading registry file: %s", e)
            return []

    async def list_agent_cards(self) -> list[AgentCard]:
        """
        Concurrently query each base URL to retrieve its agent card.
        """

        async def fetch_card(base_url: str, client: httpx.AsyncClient) -> AgentCard | None:
            try:
                resolver = A2ACardResolver(
                    base_url=base_url.rstrip("/"),
                    httpx_client=client
                )
                return await resolver.get_agent_card()
            except Exception as e:
                logger.warning("Failed to fetch agent card from %s: %s", base_url, e)
                return None

        async with httpx.AsyncClient(timeout=AGENT_DISCOVERY_TIMEOUT) as httpx_client:
            results = await asyncio.gather(
                *[fetch_card(url, httpx_client) for url in self.base_urls]
            )

        return [card for card in results if card is not None]
