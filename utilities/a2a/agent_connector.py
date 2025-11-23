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
            # If response is empty, try to get a better error message
            if not agent_response or agent_response.strip() == "":
                # Check if there's history with actual content
                if "result" in response_data and "history" in response_data["result"]:
                    history = response_data["result"]["history"]
                    # Look for the last agent message in history
                    for msg in reversed(history):
                        if msg.get("role") == "agent" and msg.get("parts"):
                            for part in msg["parts"]:
                                if part.get("kind") == "text" and part.get("text"):
                                    agent_response = part["text"]
                                    break
                            if agent_response:
                                break
                
                # Still empty? Return a helpful message
                if not agent_response or agent_response.strip() == "":
                    agent_response = "The agent processed your request but returned no text response."
        except (KeyError, IndexError, TypeError) as e:
            agent_response = f"Error parsing agent response: {str(e)}"

        return agent_response