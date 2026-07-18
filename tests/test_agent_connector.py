"""
Tests for utilities/a2a/agent_connector.py — response extraction and failure handling.
"""

from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
from a2a.client.errors import A2AClientError, A2AClientHTTPError, A2AClientTimeoutError

from utilities.a2a.agent_connector import AgentConnector


class FakeResponse:
    """Stands in for the a2a SendMessageResponse; only model_dump is used."""

    def __init__(self, data: dict):
        self._data = data

    def model_dump(self, **kwargs: Any) -> dict:
        return self._data


def _status_payload(text: str) -> dict:
    return {
        "result": {
            "status": {"message": {"parts": [{"kind": "text", "text": text}]}}
        }
    }


async def _send(connector: AgentConnector, outcome, **send_kwargs) -> str:
    """Run send_task with A2AClient patched to return or raise `outcome`."""
    with patch("utilities.a2a.agent_connector.A2AClient") as client_cls:
        instance = client_cls.return_value
        if isinstance(outcome, Exception):
            instance.send_message = AsyncMock(side_effect=outcome)
        else:
            instance.send_message = AsyncMock(return_value=outcome)
        result = await connector.send_task(message="hi", session_id="s1", **send_kwargs)
        return result, client_cls


class TestResponseExtraction:
    async def test_send_task_extracts_status_message(self, agent_card_factory):
        connector = AgentConnector(agent_card=agent_card_factory("specialist"))
        result, _ = await _send(connector, FakeResponse(_status_payload("hello there")))
        assert result == "hello there"

    async def test_send_task_falls_back_to_history(self, agent_card_factory):
        connector = AgentConnector(agent_card=agent_card_factory("specialist"))
        payload = {
            "result": {
                "status": {},
                "history": [
                    {"role": "user", "parts": [{"kind": "text", "text": "hi"}]},
                    {"role": "agent", "parts": [{"kind": "text", "text": "from history"}]},
                ],
            }
        }
        result, _ = await _send(connector, FakeResponse(payload))
        assert result == "from history"

    async def test_send_task_returns_notice_when_no_text(self, agent_card_factory):
        connector = AgentConnector(agent_card=agent_card_factory("specialist"))
        result, _ = await _send(connector, FakeResponse({"result": {}}))
        assert result == "The agent processed your request but returned no text response."

    async def test_send_task_surfaces_agent_error_payload(self, agent_card_factory):
        connector = AgentConnector(agent_card=agent_card_factory("specialist"))
        result, _ = await _send(connector, FakeResponse({"error": {"message": "boom"}}))
        assert result == "Agent error: boom"


class TestFailureHandling:
    async def test_send_task_timeout_returns_error_string(self, agent_card_factory):
        connector = AgentConnector(agent_card=agent_card_factory("specialist"))
        result, _ = await _send(connector, A2AClientTimeoutError("too slow"))
        assert result.startswith("Error: Request to agent 'specialist' timed out")

    async def test_send_task_connection_failure_returns_error_string(
        self, agent_card_factory
    ):
        connector = AgentConnector(agent_card=agent_card_factory("specialist"))
        result, _ = await _send(connector, A2AClientHTTPError(503, "connection refused"))
        assert "HTTP 503" in result
        assert "is it running?" in result

    async def test_send_task_generic_client_error_returns_error_string(
        self, agent_card_factory
    ):
        connector = AgentConnector(agent_card=agent_card_factory("specialist"))
        result, _ = await _send(connector, A2AClientError("protocol mismatch"))
        assert result.startswith("Error contacting agent 'specialist'")

    async def test_send_task_uses_provided_httpx_client(self, agent_card_factory):
        connector = AgentConnector(agent_card=agent_card_factory("specialist"))
        async with httpx.AsyncClient() as shared_client:
            _, client_cls = await _send(
                connector,
                FakeResponse(_status_payload("ok")),
                httpx_client=shared_client,
            )
        assert client_cls.call_args.kwargs["httpx_client"] is shared_client
