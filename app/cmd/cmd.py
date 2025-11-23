import asyncio
from uuid import uuid4
from a2a.types import AgentCard
from a2a.client import A2ACardResolver
import asyncclick as click
import httpx

from utilities.a2a.agent_connector import AgentConnector


@click.command()
@click.option("--agent", default="http://localhost:11000", help="Base URL of the agent")
@click.option("--session", default="0", help="Session ID (use 0 to generate a new one)")
async def cli(agent: str, session: str):
    """
    CLI to send user messages to an A2A agent using an A2A client
    and display the responses
    """

    # ✅ Correct session ID logic
    session_id = uuid4().hex if str(session) == "0" else session

    print(f"Using session ID: {session_id}")

    while True:
        prompt = await click.prompt(
            "\nWhat do you want to send to the agent? (type ':q' or 'quit' to exit)"
        )

        # Exit condition
        if prompt.strip().lower() in ["quit", ":q"]:
            break

        card: AgentCard = None

        # ✅ Resolve agent card
        async with httpx.AsyncClient(timeout=300.0) as httpx_client:
            resolver = A2ACardResolver(
                base_url=agent.rstrip("/"),
                httpx_client=httpx_client
            )

            card = await resolver.get_agent_card()

        # ✅ Send task
        connector = AgentConnector(card)
        result = await connector.send_task(
            message=prompt,
            session_id=session_id
        )

        # ✅ Print result
       # print(f"\nAgent Response:\n{result}")


if __name__ == "__main__":
    cli(_anyio_backend="asyncio")