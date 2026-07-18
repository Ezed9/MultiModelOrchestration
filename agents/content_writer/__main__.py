import click
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agents.content_writer.agent_executor import ContentWriterAgentExecutor
from utilities.config import configure_logging


@click.command()
@click.option('--host', default='localhost', help='Host for the agent server')
@click.option('--port', default=10001, type=int, help='Port for the agent server')
def main(host: str, port: int):
    """Main function to run the content writer"""
    configure_logging()

    skill = AgentSkill(
        id="content_writer_skill",
        name="content_writer_skill",
        description="A writing specialist for marketing copy, taglines, summaries, and outlines",
        tags=["writing", "copy", "summarization", "content"],
        examples=[
            "Write a product tagline for a coffee shop",
            "Summarize this text in two sentences",
        ]
    )

    agent_card = AgentCard(
        name="content_writer",
        description="A writing specialist that creates marketing copy, taglines, and summaries",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=[skill],
        capabilities=AgentCapabilities(streaming=True)
    )

    request_handler = DefaultRequestHandler(
        agent_executor=ContentWriterAgentExecutor(),
        task_store=InMemoryTaskStore()
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main()
