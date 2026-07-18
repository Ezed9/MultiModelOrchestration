"""
Base agent class providing common initialization and patterns.

Reduces code duplication across agent implementations.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator

from google.adk import Runner
from google.adk.agents import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.genai import types

from utilities.common.file_loader import load_instructions_file
from utilities.config import DEFAULT_MODEL

logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Base class for LLM agents.
    
    Provides common initialization, session management, and invocation patterns.
    Subclasses should override _build_agent() to customize agent behavior.
    """
    
    def __init__(
        self,
        name: str,
        instructions_file: str,
        description_file: str,
        model: str = DEFAULT_MODEL,
        lazy_init: bool = False,
    ):
        """
        Initialize the base agent.
        
        Args:
            name: Unique name for this agent
            instructions_file: Path to the system instructions file
            description_file: Path to the agent description file
            model: LLM model to use
            lazy_init: If True, defer agent initialization until first invoke
        """
        self.name = name
        self.model = model
        self._user_id = f"{name}_user"
        
        # Load required files
        self.system_instruction = load_instructions_file(instructions_file)
        if not self.system_instruction:
            raise RuntimeError(f"{instructions_file} is missing or empty")
        
        self.description = load_instructions_file(description_file)
        if not self.description:
            raise RuntimeError(f"{description_file} is missing or empty")
        
        # Agent and runner (may be lazy initialized)
        self._agent: LlmAgent | None = None
        self._runner: Runner | None = None
        self._init_lock = asyncio.Lock()
        
        if not lazy_init:
            self._agent = self._build_agent()
            self._runner = self._build_runner(self._agent)
    
    def _build_agent(self) -> LlmAgent:
        """
        Build the LLM agent.
        
        Override this method to add custom tools or modify agent configuration.
        
        Returns:
            Configured LlmAgent instance
        """
        return LlmAgent(
            name=self.name,
            model=self.model,
            instruction=self.system_instruction,
            description=self.description,
        )
    
    def _build_runner(self, agent: LlmAgent) -> Runner:
        """
        Build the agent runner with required services.
        
        Args:
            agent: The agent to run
            
        Returns:
            Configured Runner instance
        """
        return Runner(
            app_name=agent.name,
            agent=agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
    
    async def _ensure_initialized(self) -> None:
        """Ensure the agent is initialized (for lazy init mode)."""
        if self._agent is not None and self._runner is not None:
            return
            
        async with self._init_lock:
            # Double-check after acquiring lock
            if self._agent is not None:
                return
            
            logger.info(f"Initializing agent: {self.name}")
            self._agent = self._build_agent()
            self._runner = self._build_runner(self._agent)
    
    async def _get_or_create_session(self, session_id: str):
        """
        Get an existing session or create a new one.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Session object
        """
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
        
        return session
    
    async def invoke(
        self, query: str, session_id: str
    ) -> AsyncGenerator[dict, None]:
        """
        Invoke the agent with a query.
        
        Args:
            query: The user's input query
            session_id: Session identifier for conversation context
            
        Yields:
            Dict with 'is_task_complete', and either 'content' or 'updates'
        """
        await self._ensure_initialized()
        await self._get_or_create_session(session_id)
        
        user_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)]
        )
        
        logger.debug(f"Running agent {self.name} with query: {query[:100]}...")
        
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
