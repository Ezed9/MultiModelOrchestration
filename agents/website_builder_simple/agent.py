from typing import AsyncGenerator
from utilities.common.file_loader import load_instructions_file
from google.adk.agents import LlmAgent
from google.adk import Runner

from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService

from google.genai import types

from dotenv import load_dotenv
load_dotenv()

class WebsiteBuilderSimple:
    """
    A simple website builder agent that can create basic
    web pages using Google's development framework.
    """

    def __init__(self):
        self.system_instruction = load_instructions_file(
            "agents/website_builder_simple/instructions.txt"
        )
        if not self.system_instruction:
            raise RuntimeError(
                "agents/website_builder_simple/instructions.txt is missing or empty"
            )

        self.description = load_instructions_file(
            "agents/website_builder_simple/description.txt"
        )
        if not self.description:
            raise RuntimeError(
                "agents/website_builder_simple/description.txt is missing or empty"
            )

        self._agent = self._build_agent()
        self._user_id = "website_builder_simple_agent_user"

        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def _build_agent(self) -> LlmAgent:
        return LlmAgent(
            name="website_builder_simple",
            model="gemini-2.5-flash",
            instruction=self.system_instruction,
            description=self.description,
        )

    async def invoke(self, query: str, session_id: str) -> AsyncGenerator[dict, None]:
        """
        Streams responses from the agent.

        Expected output format:
        {
            'is_task_complete': bool,  # True if task is finished
            'updates': str,            # Progress updates (while working)
            'content': str             # Final output (when done)
        }
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
                    'is_task_complete': True,
                    'content': final_response
                }
            else:
                yield {
                    'is_task_complete': False,
                    'updates': "agent is processing your request..."
                }
