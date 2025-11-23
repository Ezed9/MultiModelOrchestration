from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from agents.host_agent.agent import HostAgent   # ✅ FIXED import
from a2a.utils import (
    new_task,
    new_agent_text_message
)
from a2a.types import TaskState
import asyncio


class HostAgentExecutor(AgentExecutor):
    """
    Connects the HostAgent to the A2A framework.
    This class controls how requests are executed and streamed.
    """

    def __init__(self):
        # Create an instance of your AI agent
        self.agent = HostAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Main executor method.
        Takes user context and streams events back.
        """

        # Get the user's query text
        query = context.get_user_input()

        # Get current task if it exists
        task = context.current_task

        # Create a new task if one does not exist
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        # Create task updater to stream updates
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            # Stream agent responses
            async for item in self.agent.invoke(query, task.context_id):

                is_task_complete = item.get("is_task_complete", False)

                # If task is still running
                if not is_task_complete:
                    message = item.get(
                        "updates",
                        "The agent is still working on your request..."
                    )
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            message,
                            task.context_id,
                            task.id
                        )
                    )

                # If task is complete
                else:
                    final_result = item.get("content", "No result received")

                    await updater.update_status(
                        TaskState.completed,
                        new_agent_text_message(
                            final_result,
                            task.context_id,
                            task.id
                        )
                    )

                    # Give time for event delivery
                    await asyncio.sleep(0.1)
                    break

        except Exception as e:
            # Handle failures
            error_message = f"An error occurred: {str(e)}"

            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    error_message,
                    task.context_id,
                    task.id
                )
            )
            raise

    async def cancel(self, request: RequestContext, event_queue: EventQueue):
        """
        Cancel operation is not supported for this agent.
        """
        raise NotImplementedError("Cancel operation is not supported")