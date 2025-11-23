import uvicorn
from a2a.types import AgentSkill, AgentCard, AgentCapabilities
import click
from a2a.server.request_handlers import DefaultRequestHandler

from agents.host_agent.agent_executor import HostAgentExecutor
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication


@click.command()
@click.option('--host', default='localhost', help='Host for the agent server')
@click.option('--port', default=11000, type=int, help='Port for the agent server')
def main(host: str, port: int):
    """Main function to run the Host Agent"""

    # Define Host Agent skill
    skill = AgentSkill(
        id="host_agent_skill",
        name="host_agent_skill",
        description="An orchestrator agent that can discover and delegate tasks to other AI agents",
        tags=["orchestration", "routing", "agents", "coordination"],
        examples=[
            "Find an agent that can build a website",
            "Delegate a task to another agent",
        ]
    )

    # Define Host Agent metadata (Agent Card)
    agent_card = AgentCard(
        name="host_agent",
        description="An orchestrator agent that manages and coordinates multiple AI agents",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=[skill],
        capabilities=AgentCapabilities(streaming=True)
    )

    # Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=HostAgentExecutor(),
        task_store=InMemoryTaskStore()
    )

    # Build server app
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    # Run the server
    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main()