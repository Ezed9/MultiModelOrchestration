"""
Base agent executor for A2A protocol.

Provides common functionality for executing agent tasks, reducing duplication
across agent implementations.
"""

import logging
from typing import Protocol, AsyncGenerator

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.utils import new_agent_text_message, new_task
from a2a.types import TaskState

logger = logging.getLogger(__name__)


class AgentProtocol(Protocol):
    """Protocol defining the interface for agents."""
    
    async def invoke(
        self, query: str, session_id: str
    ) -> AsyncGenerator[dict, None]:
        """
        Invoke the agent with a query.
        
        Args:
            query: The user's input query
            session_id: Session identifier for conversation context
            
        Yields:
            Dict with 'is_task_complete', 'content' (if complete), 
            or 'updates' (if in progress)
        """
        ...


class BaseAgentExecutor(AgentExecutor):
    """
    Base executor that handles the A2A protocol boilerplate.
    
    Subclasses only need to provide the agent instance.
    """
    
    def __init__(self, agent: AgentProtocol):
        """
        Initialize the executor with an agent.
        
        Args:
            agent: An agent implementing the AgentProtocol
        """
        self.agent = agent
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Execute a task request using the agent.
        
        Args:
            context: The request context containing user input
            event_queue: Queue for sending events back to the client
        """
        query = context.get_user_input()
        task = context.current_task
        
        if task is None:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        
        task_updater = TaskUpdater(event_queue, task.id, task.context_id)
        
        logger.info(f"Executing task {task.id} with query: {query[:100]}...")
        
        try:
            async for item in self.agent.invoke(query, task.context_id):
                is_task_complete = item.get("is_task_complete", False)
                
                if is_task_complete:
                    content = item.get("content", "")
                    logger.info(f"Task {task.id} completed successfully")
                    await task_updater.update_status(
                        TaskState.completed,
                        new_agent_text_message(
                            content,
                            task.context_id,
                            task.id,
                        ),
                    )
                    break
                else:
                    updates = item.get("updates", "Processing...")
                    await task_updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            updates,
                            task.context_id,
                            task.id,
                        ),
                    )
                    
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}", exc_info=True)
            await task_updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f"Error: {e}",
                    task.context_id,
                    task.id,
                ),
            )
            raise

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """
        Cancel a running task.
        
        Note: Currently a no-op as agents don't support cancellation.
        
        Args:
            context: The request context
            event_queue: Queue for sending events
        """
        logger.info(f"Cancel requested for context {context}")
        # Future: Implement cancellation support
