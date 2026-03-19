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

        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(
                **send_message_payload
            )
        )

        try:
            response = await a2a_client.send_message(request=request)
        except httpx.HTTPError as e:
            return f"Network error contacting agent: {e}"
        except Exception as e:
            return f"Unexpected error contacting agent: {e}"

        response_data = response.model_dump(mode="json", exclude_none=True)

        if "error" in response_data:
            return f"Agent error: {response_data['error'].get('message', response_data['error'])}"

        agent_response = ""

        try:
            parts = response_data["result"]["status"]["message"]["parts"]
            for part in parts:
                if part.get("kind") == "text" and part.get("text"):
                    agent_response = part["text"]
                    break

            # If the status message had no text, fall back to history
            if not agent_response or not agent_response.strip():
                history = response_data.get("result", {}).get("history", [])
                for msg in reversed(history):
                    if msg.get("role") == "agent" and msg.get("parts"):
                        for part in msg["parts"]:
                            if part.get("kind") == "text" and part.get("text"):
                                agent_response = part["text"]
                                break
                    if agent_response and agent_response.strip():
                        break

            if not agent_response or not agent_response.strip():
                agent_response = "The agent processed your request but returned no text response."

        except (KeyError, IndexError, TypeError) as e:
            agent_response = f"Error parsing agent response: {e}"

        return agent_response
