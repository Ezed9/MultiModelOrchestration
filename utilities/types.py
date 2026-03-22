"""
Type definitions for the MCP A2A project.

Provides TypedDict definitions for message structures and other shared types.
"""

from typing import TypedDict, NotRequired


class MessagePart(TypedDict):
    """A single part of a message."""
    text: str
    kind: NotRequired[str]


class Message(TypedDict):
    """A message in the A2A protocol."""
    messageId: str
    role: str
    parts: list[MessagePart]


class SendMessagePayload(TypedDict):
    """Payload for sending a message to an agent."""
    message: Message


class AgentResponseItem(TypedDict):
    """An item yielded from an agent's invoke method."""
    is_task_complete: bool
    content: NotRequired[str]
    updates: NotRequired[str]


class SkillInfo(TypedDict):
    """Information about a skill."""
    name: str
    description: str


class AgentInfo(TypedDict):
    """Information about an agent."""
    name: str
    description: NotRequired[str]
    url: NotRequired[str]
