"""
Agent connector for A2A protocol communication.
"""

import logging
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2AClient
from a2a.client.errors import A2AClientError, A2AClientHTTPError, A2AClientTimeoutError
from a2a.types import AgentCard, MessageSendParams, SendMessageRequest

from utilities.config import AGENT_EXECUTION_TIMEOUT

logger = logging.getLogger(__name__)


class AgentConnector:
    """
    Connects to a remote A2A agent and provides a uniform way to delegate tasks.
    """

    def __init__(self, agent_card: AgentCard):
        """
        Initialize the connector with an agent card.
        
        Args:
            agent_card: The A2A agent card containing connection info
        """
        self.agent_card = agent_card

    async def send_task(
        self,
        message: str,
        session_id: str,
        httpx_client: httpx.AsyncClient | None = None
    ) -> str:
        """
        Send a task to the agent and return the response.

        Args:
            message: The message to send to the agent
            session_id: The session ID for tracking the task
            httpx_client: Optional shared HTTP client for connection pooling

        Returns:
            The response text from the agent
        """
        if httpx_client:
            return await self._send_with_client(httpx_client, message, session_id)

        async with httpx.AsyncClient(timeout=AGENT_EXECUTION_TIMEOUT) as new_client:
            return await self._send_with_client(new_client, message, session_id)

    async def _send_with_client(
        self,
        client: httpx.AsyncClient,
        message: str,
        session_id: str
    ) -> str:
        """Send the message using the provided HTTP client."""
        a2a_client = A2AClient(
            httpx_client=client,
            agent_card=self.agent_card,
        )

        send_message_payload: dict[str, Any] = {
            "message": {
                "messageId": str(uuid4()),
                "role": "user",
                "parts": [{"text": message}]
            }
        }

        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(**send_message_payload)
        )

        # The a2a-sdk transport wraps all httpx errors into A2AClientError
        # subclasses, so catching httpx exceptions here would never fire.
        try:
            logger.debug(f"Sending message to agent: {self.agent_card.name}")
            response = await a2a_client.send_message(request=request)
        except A2AClientTimeoutError as e:
            logger.error(f"Timeout contacting agent {self.agent_card.name}: {e}")
            return (
                f"Error: Request to agent '{self.agent_card.name}' "
                f"timed out after {AGENT_EXECUTION_TIMEOUT}s"
            )
        except A2AClientHTTPError as e:
            logger.error(f"HTTP error from agent {self.agent_card.name}: {e}")
            return (
                f"Error: Could not reach agent '{self.agent_card.name}' "
                f"(HTTP {e.status_code}) - is it running?"
            )
        except A2AClientError as e:
            logger.error(f"A2A client error contacting agent {self.agent_card.name}: {e}")
            return f"Error contacting agent '{self.agent_card.name}': {e}"

        return self._extract_response(response)

    def _extract_response(self, response: Any) -> str:
        """
        Extract text response from the A2A response object.
        
        Args:
            response: The A2A response object
            
        Returns:
            Extracted text response or error message
        """
        response_data = response.model_dump(mode="json", exclude_none=True)

        if "error" in response_data:
            error_info = response_data["error"]
            error_msg = error_info.get("message", str(error_info))
            logger.warning(f"Agent returned error: {error_msg}")
            return f"Agent error: {error_msg}"

        # Try to extract from primary message parts
        agent_response = self._extract_from_status(response_data)
        
        # Fallback to history if status message is empty
        if not agent_response:
            agent_response = self._extract_from_history(response_data)
        
        if not agent_response:
            logger.warning("Agent returned no text response")
            return "The agent processed your request but returned no text response."

        return agent_response
    
    def _extract_from_status(self, response_data: dict) -> str:
        """Extract response text from status message."""
        try:
            parts = (
                response_data
                .get("result", {})
                .get("status", {})
                .get("message", {})
                .get("parts", [])
            )
            for part in parts:
                if isinstance(part, dict) and part.get("kind") == "text":
                    text = part.get("text", "").strip()
                    if text:
                        return text
        except (TypeError, AttributeError) as e:
            logger.debug(f"Could not extract from status: {e}")
        return ""
    
    def _extract_from_history(self, response_data: dict) -> str:
        """Extract response text from conversation history (fallback)."""
        try:
            history = response_data.get("result", {}).get("history", [])
            for msg in reversed(history):
                if msg.get("role") == "agent" and msg.get("parts"):
                    for part in msg["parts"]:
                        if isinstance(part, dict) and part.get("kind") == "text":
                            text = part.get("text", "").strip()
                            if text:
                                return text
        except (TypeError, AttributeError, KeyError) as e:
            logger.debug(f"Could not extract from history: {e}")
        return ""
