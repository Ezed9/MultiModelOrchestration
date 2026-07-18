from uuid import uuid4

import asyncclick as click
import httpx
from a2a.client import A2ACardResolver

from utilities.a2a.agent_connector import AgentConnector
from utilities.config import AGENT_EXECUTION_TIMEOUT, configure_logging
from utilities.skills import SkillSearch


def parse_slash_command(message: str) -> tuple[str, str] | None:
    """
    Parse a slash command from user input.
    
    Returns:
        Tuple of (skill_name, remaining_args) if message starts with /
        None if not a slash command
    """
    message = message.strip()
    if not message.startswith("/"):
        return None
    
    # Remove leading slash and split on first space
    parts = message[1:].split(maxsplit=1)
    skill_name = parts[0] if parts else ""
    remaining = parts[1] if len(parts) > 1 else ""
    
    return (skill_name, remaining)


def format_skill_message(skill_name: str, instructions: str, user_args: str) -> str:
    """
    Format a message that includes skill instructions for the Host Agent.
    """
    message = f"[SKILL: {skill_name}]\n\n"
    message += f"Follow these instructions:\n{instructions}\n\n"
    if user_args:
        message += f"User request: {user_args}"
    return message


@click.command()
@click.option("--agent", default="http://localhost:11000", help="Base URL of the agent")
@click.option("--session", default="0", help="Session ID (use 0 to generate a new one)")
async def cli(agent: str, session: str):
    """
    CLI to send user messages to an A2A agent using an A2A client
    and display the responses.
    
    Supports slash commands to invoke skills (e.g., /build-landing-page).
    """

    configure_logging()
    session_id = uuid4().hex if str(session) == "0" else session
    skill_search = SkillSearch()

    print(f"Using session ID: {session_id}")
    print("Tip: Use /skill-name to invoke a skill (e.g., /list-capabilities)")

    async with httpx.AsyncClient(timeout=AGENT_EXECUTION_TIMEOUT) as httpx_client:
        try:
            resolver = A2ACardResolver(
                base_url=agent.rstrip("/"),
                httpx_client=httpx_client
            )
            card = await resolver.get_agent_card()
        except Exception as e:
            print(f"Error resolving agent: {e}")
            return

        connector = AgentConnector(card)

        while True:
            try:
                prompt = await click.prompt(
                    "\nWhat do you want to send to the agent? (type ':q' or 'quit' to exit)"
                )

                if prompt.strip().lower() in ["quit", ":q"]:
                    break

                # Check for slash command
                slash_cmd = parse_slash_command(prompt)
                if slash_cmd:
                    skill_name, user_args = slash_cmd
                    skill = skill_search.search_by_name(skill_name)
                    
                    if not skill:
                        # Show available skills
                        available = skill_search.list_all()
                        print(f"\nUnknown skill: /{skill_name}")
                        if available:
                            print("Available skills:")
                            for s in available:
                                print(f"  /{s.name} — {s.description[:60]}...")
                        else:
                            print("No skills available.")
                        continue
                    
                    # Inject skill instructions into message
                    prompt = format_skill_message(skill.name, skill.instructions, user_args)
                    print(f"\n[Invoking skill: {skill.name}]")

                result = await connector.send_task(
                    message=prompt,
                    session_id=session_id,
                    httpx_client=httpx_client
                )

                print(f"\nAgent Response:\n{result}")

            except click.Abort:
                break
            except Exception as e:
                print(f"\nError sending message: {e}")


if __name__ == "__main__":
    cli(_anyio_backend="asyncio")
