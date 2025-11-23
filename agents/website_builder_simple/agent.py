from typing import AsyncIterable
from utilities.common.file_loader import load_instructions_file
from google.adk.agents import LlmAgent
from google.adk import Runner

from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService

from google.genai import types


class WebsiteBuilderSimple:
    """
    A simple website builder agent that can create basic
    web pages using Google's development framework.
    """

    def __init__(self):
        # Load system instructions (rules for the agent)
        self.system_instruction = load_instructions_file(
            "agents/website_builder_simple/instructions.txt"
        )

        # Load agent description text
        self.description = load_instructions_file(
            "agents/website_builder_simple/description.txt"
        )

        # Build the LLM agent
        self._agent = self._build_agent()

        # Unique ID for the user session
        self._user_id = "website_builder_simple_agent_user"

        # Create a Runner to manage sessions, memory, and artifacts
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def _build_agent(self) -> LlmAgent:
        """
        Builds and returns the LLM agent configuration.
        """
        return LlmAgent(
            name="website_builder_simple",
            model="gemini-2.5-flash",
            instruction=self.system_instruction,
            description=self.description,
        )

    async def invoke(self, query: str, session_id: str) -> AsyncIterable[dict]:
        """
        Streams responses from the agent.

        Expected output format:
        {
            'is_task_complete': bool,  # True if task is finished
            'updates': str,            # Progress updates (while working)
            'content': str             # Final output (when done)
        }
        """

        # Try to get an existing session
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            session_id=session_id,
            user_id=self._user_id,
        )

        # If session doesn’t exist, create a new one
        if not session:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                session_id=session_id,
                user_id=self._user_id,
            )

        # Wrap the user query into Gemini-compatible content
        user_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)]
        )

        # Stream the model responses asynchronously
        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=session_id,
            new_message=user_content,
        ):
            print_json_response(event, "=====NEW EVENT=====")
            # If this is the final response from the model
            if event.is_final_response:
                final_response = ""

                # Extract text from the last part of the response
                if event.content and event.content.parts and event.content.parts[-1].text:
                    final_response = event.content.parts[-1].text

                # Send final result to caller
                yield {
                    'is_task_complete': True,
                    'content': final_response
                }

            # If the agent is still processing
            else:
                yield {
                    'is_task_complete': False,
                    'updates': "agent is processing your request.... "
                }