from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class Message:
    """
    Represents a single message in the conversation history.

    Messages can represent user input, assistant responses, or the results
    of tool executions. The role determines how the message is interpreted
    by the LLM API.

    Attributes:
        role: Message role (user, assistant, or tool_result)
        content: The message content
        tool_use_id: Optional ID linking tool results to tool calls
    """

    role: Literal["user", "assistant", "tool_result"]
    content: str
    tool_use_id: Optional[str] = None

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        # Truncate content for readability
        preview = (
            self.content[:50] + "..."
            if len(self.content) > 50
            else self.content
        )

        if self.tool_use_id:
            return (
                f"#<Message role={self.role} "
                f"content={preview} "
                f"tool_use_id={self.tool_use_id}>"
            )
        return f"#<Message role={self.role} content={preview}>"
