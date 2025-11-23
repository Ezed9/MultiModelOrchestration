from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater, Task
from agents.website_builder_simple.agent import WebsiteBuilderSimple
from a2a.utils import (
    new_task,
    new_agent_text_message
)
from a2a.types import TaskState
from a2a.server.errors import ServerError, UnsupportedOperationError

import asyncio


class WebsiteBuilderSimpleAgentExecutor(AgentExecutor):
    """
    Connects your WebsiteBuilderSimple agent to the A2A framework.
    This class controls how requests are executed and streamed.
    """

    def __init__(self):
        # Create an instance of your AI agent
        self.agent = WebsiteBuilderSimple()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Main executor method.
        Takes user context and streams events back.
        """

        # Collect user's input text
        query = context.get_user_input()

        # Get the current task
        task = context.current_task

        # If no task exists, create a new one
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        # Create a helper object to update task progress
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            # Stream results from your AI agent
            async for item in self.agent.invoke(query, task.context_id):

                # Check if task is complete
                is_task_complete = item.get("is_task_complete", False)

                # If still processing, send progress updates
                if not is_task_complete:
                    message = item.get(
                        "updates",
                        "The Agent is still working on your request"
                    )
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            message,
                            task.context_id,
                            task.id
                        )
                    )
                else:
                    # Final result
                    final_result = item.get("content", "no result received")

                    await updater.update_status(
                        TaskState.completed,
                        new_agent_text_message(
                            final_result,
                            task.context_id,
                            task.id
                        )
                    )

                    # Small delay to ensure message is delivered
                    await asyncio.sleep(0.1)
                    break

        except Exception as e:
            # Error handling for failures
            error_message = f"An error occurred: {str(e)}"

            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    error_message,
                    task.context_id,
                    task.id
                )
            )

            # Re-throw the error
            raise

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> Task | None:
        """
        Cancel operation is not supported for this agent.
        """
        raise ServerError(error=UnsupportedOperationError())