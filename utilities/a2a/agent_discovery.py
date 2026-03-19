import os
import json
import asyncio
import logging
from typing import List
from urllib.parse import urlparse
from a2a.types import AgentCard
from a2a.client import A2ACardResolver

import httpx

logger = logging.getLogger(__name__)

_ALLOWED_URL_SCHEMES = {"http", "https"}


class AgentDiscovery:
    """
    Discovers A2A Agents by reading a registry file of URLs and
    querying each one's /.well-known/agent.json endpoint to retrieve an AgentCard.
    """

    def __init__(self, registry_file: str = None):
        if registry_file:
            self.registry_file = registry_file
        else:
            self.registry_file = os.path.join(
                os.path.dirname(__file__),
                "agent_registry.json"
            )

        self.base_urls = self._load_registry()

    def _load_registry(self) -> List[str]:
        """
        Load and validate agent URLs from the registry JSON file.
        """
        try:
            with open(self.registry_file, "r") as f:
                data = json.load(f)

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

        except FileNotFoundError:
            raise FileNotFoundError(
                f"Agent registry file not found: {self.registry_file}. "
                "Check that the file exists and the path is correct."
            )

        except json.JSONDecodeError:
            logger.error("Registry file contains invalid JSON: %s", self.registry_file)
            return []

        except Exception as e:
            logger.error("Error loading registry file: %s", e)
            return []

    async def list_agent_cards(self) -> List[AgentCard]:
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

        async with httpx.AsyncClient(timeout=30.0) as httpx_client:
            results = await asyncio.gather(
                *[fetch_card(url, httpx_client) for url in self.base_urls]
            )

        return [card for card in results if card is not None]
