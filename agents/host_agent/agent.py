from typing import AsyncGenerator
from uuid import uuid4
import asyncio

from utilities.a2a.agent_discovery import AgentDiscovery
from utilities.a2a.agent_connector import AgentConnector
from utilities.common.file_loader import load_instructions_file

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

    # ---------------- BUILD ---------------- #

    async def _init_agent(self):
        """Async-safe lazy initializer, guarded by a lock to prevent concurrent init."""
        async with self._init_lock:
            # Another coroutine may have finished init while we waited on the lock
            if self._agent is not None:
                return

            await self.mcp_connector.load_all_tools()
            mcp_tools = self.mcp_connector.get_tools()

            agent = LlmAgent(
                name="host_agent",
                model="gemini-2.5-flash",
                instruction=self.system_instruction,
                description=self.description,
                tools=[
                    FunctionTool(self._delegate_task),
                    FunctionTool(self._list_agents),
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
