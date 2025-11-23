import os
import json
from typing import List
from a2a.types import AgentCard
from a2a.client import A2ACardResolver

import httpx


class AgentDiscovery:
    """
    Discovers A2A Agents by reading a registry file of URLs and
    querying each one's /.well-known/agent.json endpoint to retrieve an AgentCard.
    """

    def __init__(self, registry_file: str = None):
        # Set registry file path
        if registry_file:
            self.registry_file = registry_file
        else:
            self.registry_file = os.path.join(
                os.path.dirname(__file__),
                "agent_registry.json"
            )

        # Load base URLs
        self.base_urls = self._load_registry()

    def _load_registry(self) -> List[str]:
        """
        Load and parse the registry JSON file into a list of URLs
        """

        try:
            with open(self.registry_file, "r") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError("Registry file must contain a list of URLs")

            return data

        except FileNotFoundError:
            print(f"Registry file not found: {self.registry_file}")
            return []

        except json.JSONDecodeError:
            print("Registry file contains invalid JSON")
            return []

        except Exception as e:
            print(f"Error loading registry file: {e}")
            return []

    async def list_agent_cards(self) -> List[AgentCard]:
        """
        Query each base URL to retrieve its agent card.
        """

        cards: List[AgentCard] = []

        async with httpx.AsyncClient(timeout=300.0) as httpx_client:
            for base_url in self.base_urls:   # ✅ FIXED name
                try:
                    resolver = A2ACardResolver(
                        base_url=base_url.rstrip("/"),
                        httpx_client=httpx_client
                    )

                    card = await resolver.get_agent_card()
                    cards.append(card)

                except Exception as e:
                    print(f"Failed to fetch agent card from {base_url}: {e}")

        return cards