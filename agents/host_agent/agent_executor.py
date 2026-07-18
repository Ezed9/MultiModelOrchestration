"""
Host Agent Executor.

Bridges the HostAgent (orchestrator) with the A2A protocol.
"""

from agents.host_agent.agent import HostAgent
from utilities.a2a.base_agent_executor import BaseAgentExecutor


class HostAgentExecutor(BaseAgentExecutor):
    """Executor for the Host Agent (orchestrator)."""
    
    def __init__(self):
        super().__init__(HostAgent())