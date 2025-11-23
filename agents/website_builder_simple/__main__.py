import uvicorn
from a2a.types import AgentSkill, AgentCard, AgentCapabilities
import click
from a2a.server.request_handlers import DefaultRequestHandler

from agents.website_builder_simple.agent_executor import WebsiteBuilderSimpleAgentExecutor
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication


@click.command()
@click.option('--host', default='localhost', help='Host for the agent server')
@click.option('--port', default=10000, type=int, help='Port for the agent server')
def main(host: str, port: int):
    """Main function to run the website builder"""

    # Define agent skill
    skill = AgentSkill(
        id="website_builder_simple_skill",
        name="website_builder_simple_skill",
        description="A simple website builder agent that can build basic web pages",
        tags=["website", "html", "css", "javascript"],
        examples=[
            "Create a simple website with header and footer",
            "Create a landing page for a product with a call to action button",
        ]
    )

    # Define agent metadata (Agent Card)
    agent_card = AgentCard(
        name="website_builder_simple",
        description="A simple website builder that can create basic web pages",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=[skill],
        capabilities=AgentCapabilities(streaming=True)
    )

    # Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=WebsiteBuilderSimpleAgentExecutor(),
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