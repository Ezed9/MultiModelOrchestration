from typing import AsyncGenerator
from uuid import uuid4
import asyncio

from utilities.a2a.agent_discovery import AgentDiscovery
from utilities.a2a.agent_connector import AgentConnector
from utilities.common.file_loader import load_instructions_file
from utilities.skills import SkillSearch

from google.adk.agents import LlmAgent
from google.adk import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.tools.function_tool import FunctionTool

from google.genai import types

from utilities.mcp.mcp_connect import MCPConnect
from a2a.types import AgentCard

from dotenv import load_dotenv
load_dotenv()


class HostAgent:
    """
    Orchestrator agent
    """

    def __init__(self):
        self.system_instruction = load_instructions_file(
            "agents/host_agent/instructions.txt"
        )
        if not self.system_instruction:
            raise RuntimeError("agents/host_agent/instructions.txt is missing or empty")

        self.description = load_instructions_file(
            "agents/host_agent/description.txt"
        )
        if not self.description:
            raise RuntimeError("agents/host_agent/description.txt is missing or empty")

        self._user_id = "host_agent_user"
        # Stored per-invoke so _delegate_task can reuse the caller's session
        self._current_session_id: str | None = None

        self.agent_discovery = AgentDiscovery()
        self.mcp_connector = MCPConnect()
        self.skill_search = SkillSearch()

        self._agent = None
        self._runner = None
        self._init_lock = asyncio.Lock()

    # ---------------- TOOLS ---------------- #

    async def _list_agents(self) -> list[dict]:
        cards: list[AgentCard] = await self.agent_discovery.list_agent_cards()
        return [card.model_dump(exclude_none=True) for card in cards]

    async def _delegate_task(self, agent_name: str, message: str) -> str:
        cards = await self.agent_discovery.list_agent_cards()
        matched = None

        for card in cards:
            if card.name.lower() == agent_name.lower():
                matched = card
                break

        if not matched:
            return f"Agent '{agent_name}' not found"

        connector = AgentConnector(agent_card=matched)

        # Reuse the caller's session so downstream agents share conversation context
        session_id = self._current_session_id or str(uuid4())

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
        Invoke a skill by name. The skill instructions will guide your actions.
        
        Args:
            skill_name: Name of the skill to invoke (e.g., "build-landing-page")
            user_context: Additional context or requirements from the user
            
        Returns:
            Instructions for how to execute this skill, which you should follow.
        """
        skill = self.skill_search.search_by_name(skill_name)
        
        if not skill:
            available = self.skill_search.list_all()
            skill_names = [s.name for s in available]
            return f"Skill '{skill_name}' not found. Available skills: {', '.join(skill_names)}"
        
        # Return the skill instructions for the agent to follow
        response = f"[Executing skill: {skill.name}]\n\n"
        response += f"Instructions to follow:\n{skill.instructions}\n\n"
        if user_context:
            response += f"User context: {user_context}"
        return response

    # ---------------- BUILD ---------------- #

    async def _init_agent(self):
        """Async-safe lazy initializer, guarded by a lock to prevent concurrent init."""
        async with self._init_lock:
            # Another coroutine may have finished init while we waited on the lock
            if self._agent is not None:
                return

            await self.mcp_connector.load_all_tools()
            mcp_tools = self.mcp_connector.get_tools()

            # Load skills and build skill awareness for system prompt
            skills = self.skill_search.list_all()
            skill_info = ""
            if skills:
                skill_info = "\n\nAvailable skills (invoke with _invoke_skill or _list_skills):\n"
                for skill in skills:
                    skill_info += f"- {skill.name}: {skill.description}\n"

            agent = LlmAgent(
                name="host_agent",
                model="gemini-2.5-flash",
                instruction=self.system_instruction + skill_info,
                description=self.description,
                tools=[
                    FunctionTool(self._delegate_task),
                    FunctionTool(self._list_agents),
                    FunctionTool(self._list_skills),
                    FunctionTool(self._invoke_skill),
                    *mcp_tools
                ]
            )

            runner = Runner(
                app_name=agent.name,
                agent=agent,
                artifact_service=InMemoryArtifactService(),
                session_service=InMemorySessionService(),
                memory_service=InMemoryMemoryService(),
            )

            # Assign together so both are always set or neither is
            self._agent = agent
            self._runner = runner

    # ---------------- INVOKE ---------------- #

    async def invoke(self, query: str, session_id: str) -> AsyncGenerator[dict, None]:

        if self._agent is None or self._runner is None:
            await self._init_agent()

        self._current_session_id = session_id

        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            session_id=session_id,
            user_id=self._user_id,
        )

        if not session:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                session_id=session_id,
                user_id=self._user_id,
            )

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
                    "updates": "agent is processing your request..."
                }
