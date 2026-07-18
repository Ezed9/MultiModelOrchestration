"""
Website Builder Simple Agent Executor.

Bridges the WebsiteBuilderSimple agent with the A2A protocol.
"""

from agents.website_builder_simple.agent import WebsiteBuilderSimple
from utilities.a2a.base_agent_executor import BaseAgentExecutor


class WebsiteBuilderSimpleAgentExecutor(BaseAgentExecutor):
    """Executor for the Website Builder Simple agent."""
    
    def __init__(self):
        super().__init__(WebsiteBuilderSimple())