from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from boukensha.tasks.base import Base

from boukensha.message import Message
from boukensha.tool import Tool


class Context:
    """
    Holds complete state for making API calls to an LLM.

    The Context manages all the components needed for an API call:
    conversation messages, available tools, system prompt, and task
    association. It provides a central place to manage agent state.

    Attributes:
        task: Task class reference (e.g., Player)
        system: System prompt string
        messages: Conversation history
        tools: Available tools by name
    """

    def __init__(self, task: type[Base], system: Optional[str] = None) -> None:
        """
        Initialize a new context.

        Args:
            task: Task class (not instance) to associate with
            system: Optional system prompt
        """
        self._task = task
        self._system = system
        self._messages: List[Message] = []
        self._tools: Dict[str, Tool] = {}

    @property
    def task(self) -> type[Base]:
        """Get the associated task class."""
        return self._task

    @property
    def system(self) -> Optional[str]:
        """Get the system prompt."""
        return self._system

    @property
    def messages(self) -> List[Message]:
        """Get the message history."""
        return self._messages

    @property
    def tools(self) -> Dict[str, Tool]:
        """Get the registered tools."""
        return self._tools

    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool for use in this context.

        Args:
            tool: Tool to register
        """
        self._tools[tool.name] = tool

    def add_message(
        self, role: str, content: Any, tool_use_id: Optional[str] = None
    ) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: Message role (user, assistant, tool_result)
            content: Message content (string or list of content blocks)
            tool_use_id: Optional tool use ID for tool_result messages

        Note:
            Content can be either a string (simple messages) or a list of
            content blocks (assistant messages with tool calls). The backends
            handle both formats appropriately.
        """
        self._messages.append(
            Message(role=role, content=content, tool_use_id=tool_use_id)  # type: ignore
        )

    def clear_messages(self) -> None:
        """
        Drop all conversation history, keeping tools and system prompt intact.

        Used by the REPL's /clear command to reset the conversation while
        preserving the configured tools and system prompt.
        """
        self._messages = []

    def tool_count(self) -> int:
        """Get the number of registered tools."""
        return len(self._tools)

    def turn_count(self) -> int:
        """Get the total number of messages in the conversation."""
        return len(self._messages)

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        task_name = self._task.task_name() if self._task else "None"
        return f"#<Context task={task_name} turns={self.turn_count()} tools={self.tool_count()}>"

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return str(self)
