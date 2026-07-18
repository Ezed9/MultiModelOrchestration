"""
Tests for agents/host_agent/agent.py — task routing via _delegate_task.

HostAgent is constructed with lazy init, so no LLM or API key is needed;
discovery and the connector are stubbed.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from agents.host_agent.agent import HostAgent


@pytest.fixture
def host(agent_card_factory):
    agent = HostAgent()
    cards = [
        agent_card_factory("website_builder_simple"),
        agent_card_factory("content_writer"),
    ]
    agent.agent_discovery = SimpleNamespace(
        list_agent_cards=AsyncMock(return_value=cards)
    )
    return agent


def _patch_connector(response: str = "done"):
    patcher = patch("agents.host_agent.agent.AgentConnector")
    connector_cls = patcher.start()
    connector_cls.return_value.send_task = AsyncMock(return_value=response)
    return patcher, connector_cls


class TestDelegateTask:
    async def test_delegate_task_routes_to_matching_agent(self, host):
        patcher, connector_cls = _patch_connector()
        try:
            result = await host._delegate_task("content_writer", "write a tagline")
            assert result == "done"
            routed_card = connector_cls.call_args.kwargs["agent_card"]
            assert routed_card.name == "content_writer"
        finally:
            patcher.stop()

    async def test_delegate_task_is_case_insensitive(self, host):
        patcher, connector_cls = _patch_connector()
        try:
            result = await host._delegate_task("Content_Writer", "write a tagline")
            assert result == "done"
            assert connector_cls.call_args.kwargs["agent_card"].name == "content_writer"
        finally:
            patcher.stop()

    async def test_delegate_task_unknown_agent_lists_available(self, host):
        result = await host._delegate_task("nonexistent_agent", "hello")
        assert "not found" in result
        assert "website_builder_simple" in result
        assert "content_writer" in result

    async def test_delegate_task_rejects_empty_agent_name(self, host):
        result = await host._delegate_task("", "hello")
        assert result.startswith("Error:")
        host.agent_discovery.list_agent_cards.assert_not_called()

    async def test_delegate_task_reuses_current_session_id(self, host):
        host._current_session_id = "session-42"
        patcher, connector_cls = _patch_connector()
        try:
            await host._delegate_task("content_writer", "write a tagline")
            send_kwargs = connector_cls.return_value.send_task.call_args.kwargs
            assert send_kwargs["session_id"] == "session-42"
        finally:
            patcher.stop()


class TestListAgents:
    async def test_list_agents_returns_card_dicts(self, host):
        agents = await host._list_agents()
        assert [a["name"] for a in agents] == [
            "website_builder_simple",
            "content_writer",
        ]
        assert all(isinstance(a, dict) for a in agents)
