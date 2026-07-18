"""
Tests for utilities/a2a/agent_discovery.py — registry loading and card fetching.
"""

import json

import httpx
import pytest

from utilities.a2a.agent_discovery import AgentDiscovery


def _install_mock_transport(monkeypatch, handler):
    """Make AgentDiscovery's httpx.AsyncClient route through a MockTransport."""
    real_client = httpx.AsyncClient

    def factory(**kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(**kwargs)

    monkeypatch.setattr("utilities.a2a.agent_discovery.httpx.AsyncClient", factory)


def _card_response(card) -> httpx.Response:
    return httpx.Response(
        200, json=card.model_dump(mode="json", by_alias=True, exclude_none=True)
    )


class TestLoadRegistry:
    """Registry file parsing and URL validation."""

    def test_load_registry_from_file(self, registry_file):
        discovery = AgentDiscovery(registry_file=registry_file)
        assert discovery.base_urls == [
            "http://localhost:10000",
            "http://localhost:11000",
        ]

    def test_load_registry_skips_disallowed_schemes(self, tmp_path):
        path = tmp_path / "registry.json"
        path.write_text(
            json.dumps(
                ["http://localhost:10000", "file:///etc/passwd", "ftp://evil.host"]
            )
        )
        discovery = AgentDiscovery(registry_file=path)
        assert discovery.base_urls == ["http://localhost:10000"]

    def test_load_registry_skips_non_string_entries(self, tmp_path):
        path = tmp_path / "registry.json"
        path.write_text(json.dumps(["http://localhost:10000", 42, {"url": "x"}, None]))
        discovery = AgentDiscovery(registry_file=path)
        assert discovery.base_urls == ["http://localhost:10000"]

    def test_load_registry_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            AgentDiscovery(registry_file=tmp_path / "does_not_exist.json")

    def test_load_registry_invalid_json_returns_empty(self, tmp_path):
        path = tmp_path / "registry.json"
        path.write_text("{this is not json")
        discovery = AgentDiscovery(registry_file=path)
        assert discovery.base_urls == []


class TestListAgentCards:
    """Concurrent agent-card fetching over mocked HTTP."""

    async def test_list_agent_cards_fetches_all_cards(
        self, tmp_path, monkeypatch, agent_card_factory
    ):
        path = tmp_path / "registry.json"
        path.write_text(json.dumps(["http://localhost:10000", "http://localhost:10001"]))

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/.well-known/agent-card.json"
            return _card_response(agent_card_factory(f"agent_{request.url.port}"))

        _install_mock_transport(monkeypatch, handler)
        cards = await AgentDiscovery(registry_file=path).list_agent_cards()
        assert sorted(card.name for card in cards) == ["agent_10000", "agent_10001"]

    async def test_list_agent_cards_skips_failed_endpoint(
        self, tmp_path, monkeypatch, agent_card_factory
    ):
        path = tmp_path / "registry.json"
        path.write_text(json.dumps(["http://localhost:10000", "http://localhost:10001"]))

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.port == 10000:
                return httpx.Response(500, text="internal error")
            return _card_response(agent_card_factory("healthy_agent"))

        _install_mock_transport(monkeypatch, handler)
        cards = await AgentDiscovery(registry_file=path).list_agent_cards()
        assert [card.name for card in cards] == ["healthy_agent"]
