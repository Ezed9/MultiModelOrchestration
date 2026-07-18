"""
Content Writer Agent Executor.

Bridges the ContentWriter agent with the A2A protocol.
"""

from agents.content_writer.agent import ContentWriter
from utilities.a2a.base_agent_executor import BaseAgentExecutor


class ContentWriterAgentExecutor(BaseAgentExecutor):
    """Executor for the Content Writer agent."""

    def __init__(self):
        super().__init__(ContentWriter())
