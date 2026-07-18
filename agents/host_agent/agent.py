"""
Host Agent - Orchestrator for the multi-agent system.

Routes user requests to specialist agents or MCP tools.
"""

import logging
from collections.abc import AsyncGenerator
from uuid import uuid4

from a2a.types import AgentCard
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.function_tool import FunctionTool
from google.genai import types

from utilities.a2a.agent_connector import AgentConnector
from utilities.a2a.agent_discovery import AgentDiscovery
from utilities.common.base_agent import BaseAgent
from utilities.config import DEFAULT_MODEL
from utilities.mcp.mcp_connect import MCPConnect
from utilities.skills import SkillSearch

load_dotenv()

logger = logging.getLogger(__name__)


class HostAgent(BaseAgent):
    """
    Orchestrator agent that routes requests to specialist agents and tools.
    """

    def __init__(self):
        super().__init__(
            name="host_agent",
            instructions_file="agents/host_agent/instructions.txt",
            description_file="agents/host_agent/description.txt",
            model=DEFAULT_MODEL,
            lazy_init=True,  # Defer init until MCP tools are loaded
        )
        
        # Stored per-invoke so _delegate_task can reuse the caller's session
        self._current_session_id: str | None = None

        self.agent_discovery = AgentDiscovery()
        self.mcp_connector = MCPConnect()
        self.skill_search = SkillSearch()
        
        logger.info("HostAgent created (lazy initialization)")

    # ---------------- TOOLS ---------------- #

    async def _list_agents(self) -> list[dict]:
        """List all available agents in the system."""
        cards: list[AgentCard] = await self.agent_discovery.list_agent_cards()
        return [card.model_dump(exclude_none=True) for card in cards]

    async def _delegate_task(self, agent_name: str, message: str) -> str:
        """
        Delegate a task to another agent.
        
        Args:
            agent_name: Name of the agent to delegate to
            message: The task/message to send to the agent
            
        Returns:
            Response from the agent
        """
        if not agent_name or not isinstance(agent_name, str):
            return "Error: agent_name must be a non-empty string"
        
        cards = await self.agent_discovery.list_agent_cards()
        matched = None

        for card in cards:
            if card.name.lower() == agent_name.lower():
                matched = card
                break

        if not matched:
            available = [c.name for c in cards]
            return f"Agent '{agent_name}' not found. Available: {', '.join(available)}"

        connector = AgentConnector(agent_card=matched)
        session_id = self._current_session_id or str(uuid4())
        
        logger.info(f"Delegating to agent '{agent_name}': {message[:50]}...")

        return await connector.send_task(
            message=message,
            session_id=session_id
        )

    async def _list_skills(self) -> list[dict]:
        """List all available skills with their names and descriptions."""
        skills = self.skill_search.list_all()
        return [
            {"name": skill.name, "description": skill.description}
            for skill in skills
        ]

    async def _invoke_skill(self, skill_name: str, user_context: str = "") -> str:
        """
        Invoke a skill by name.
        
        Args:
            skill_name: Name of the skill to invoke (e.g., "build-landing-page")
            user_context: Additional context or requirements from the user
            
        Returns:
            Instructions for how to execute this skill
        """
        skill = self.skill_search.search_by_name(skill_name)
        
        if not skill:
            available = self.skill_search.list_all()
            skill_names = [s.name for s in available]
            return f"Skill '{skill_name}' not found. Available skills: {', '.join(skill_names)}"
        
        response = f"[Executing skill: {skill.name}]\n\n"
        response += f"Instructions to follow:\n{skill.instructions}\n\n"
        if user_context:
            response += f"User context: {user_context}"
        return response

    # ---------------- BUILD ---------------- #

    def _build_agent(self, agent_cards: list[AgentCard] | None = None) -> LlmAgent:
        """Build the agent with all tools loaded."""
        # This is called during _ensure_initialized after MCP tools are loaded
        mcp_tools = self.mcp_connector.get_tools()

        # Discovered specialist agents, injected so routing needs no hardcoded names
        agent_info = ""
        if agent_cards:
            agent_info = "\n\nAvailable specialist agents (delegate with _delegate_task):\n"
            for card in agent_cards:
                agent_info += f"- {card.name}: {card.description}\n"

        # Load skills and build skill awareness for system prompt
        skills = self.skill_search.list_all()
        skill_info = ""
        if skills:
            skill_info = "\n\nAvailable skills (invoke with _invoke_skill or _list_skills):\n"
            for skill in skills:
                skill_info += f"- {skill.name}: {skill.description}\n"

        return LlmAgent(
            name=self.name,
            model=self.model,
            instruction=self.system_instruction + agent_info + skill_info,
            description=self.description,
            tools=[
                FunctionTool(self._delegate_task),
                FunctionTool(self._list_agents),
                FunctionTool(self._list_skills),
                FunctionTool(self._invoke_skill),
                *mcp_tools
            ]
        )
    
    async def _ensure_initialized(self) -> None:
        """Initialize agent after loading MCP tools."""
        if self._agent is not None and self._runner is not None:
            return
            
        async with self._init_lock:
            if self._agent is not None:
                return
            
            logger.info("Loading MCP tools...")
            await self.mcp_connector.load_all_tools()

            logger.info("Discovering specialist agents...")
            agent_cards = await self.agent_discovery.list_agent_cards()

            logger.info("Building HostAgent with tools...")
            self._agent = self._build_agent(agent_cards)
            self._runner = self._build_runner(self._agent)
            logger.info("HostAgent initialization complete")

    # ---------------- INVOKE ---------------- #

    async def invoke(self, query: str, session_id: str) -> AsyncGenerator[dict, None]:
        """
        Invoke the host agent with a query.
        
        Args:
            query: The user's input query
            session_id: Session identifier for conversation context
            
        Yields:
            Dict with 'is_task_complete', and either 'content' or 'updates'
        """
        await self._ensure_initialized()
        
        self._current_session_id = session_id
        await self._get_or_create_session(session_id)

        user_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)]
        )

        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=session_id,
            new_message=user_content,
        ):
            if event.is_final_response():
                final_response = ""

                if event.content and event.content.parts:
                    final_response = "".join(
                        p.text for p in event.content.parts if p.text
                    )

                yield {
                    "is_task_complete": True,
                    "content": final_response
                }
            else:
                yield {
                    "is_task_complete": False,
                    "updates": "Agent is processing your request..."
                }
