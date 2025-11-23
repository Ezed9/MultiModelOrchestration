from typing import Any
from uuid import uuid4
from a2a.types import AgentCard, SendMessageRequest, MessageSendParams
import httpx
from a2a.client import A2AClient


class AgentConnector:
    """
    Connects to a remote A2A agent and provides a uniform way to delegate tasks
    """

    def __init__(self, agent_card: AgentCard):
        self.agent_card = agent_card

    async def send_task(
        self,
        message: str,
        session_id: str,
        httpx_client: httpx.AsyncClient | None = None
    ) -> str:
        """
        Send a task to the agent and return the response

        Args:
            message (str): The message to send to the agent
            session_id (str): The session ID for tracking the task
            httpx_client (httpx.AsyncClient, optional): Shared HTTP client

        Returns:
            str: The response from the agent
        """

        # Use provided client or create a new one
        if httpx_client:
            return await self._send_with_client(httpx_client, message, session_id)

        async with httpx.AsyncClient(timeout=300.0) as new_client:
            return await self._send_with_client(new_client, message, session_id)

    async def _send_with_client(
        self,
        client: httpx.AsyncClient,
        message: str,
        session_id: str
    ) -> str:
        a2a_client = A2AClient(
            httpx_client=client,
            agent_card=self.agent_card,
        )

        # ✅ Corrected payload structure
        send_message_payload: dict[str, Any] = {
            "message": {
                "messageId": str(uuid4()),
                "role": "user",
                "parts": [
                    {
                        "text": message
                    }
                ]
            }
        }

        # ✅ Build request
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(
                **send_message_payload
            )
        )

        # ✅ Send message
        response = await a2a_client.send_message(request=request)

        # ✅ Convert response to JSON
        response_data = response.model_dump(mode="json", exclude_none=True)

        # ✅ Safely extract text
        try:
            agent_response = (
                response_data["result"]["status"]["message"]["parts"][0]["text"]
            )
        except (KeyError, IndexError, TypeError):
            agent_response = "No response from agent"

        return agent_response