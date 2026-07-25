"""
Anthropic Claude API backend.

Serializes context into Anthropic's Messages API format.
https://docs.anthropic.com/claude/reference/messages_post
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List

from boukensha.backends.base import Base

if TYPE_CHECKING:
    from boukensha.context import Context
    from boukensha.message import Message
    from boukensha.tool import Tool


class Anthropic(Base):
    """
    Backend for Anthropic's Claude API.

    Anthropic uses a straightforward format:
    - System prompt is separate from messages
    - Messages are simple {role, content} objects
    - Tools use input_schema format
    - Supports tool_result messages with special serialization
    """

    BASE_URL = "https://api.anthropic.com/v1/messages"

    MODELS: Dict[str, Dict[str, Any]] = {
        "claude-haiku-4-5": {
            "context_window": 200_000,
            "cost_per_million": {"input": 1.0, "output": 5.0},
            "usage_unit": "tokens",
        },
        "claude-haiku-4-5-20251001": {
            "context_window": 200_000,
            "cost_per_million": {"input": 1.0, "output": 5.0},
            "usage_unit": "tokens",
        },
        "claude-sonnet-4-6": {
            "context_window": 1_000_000,
            "cost_per_million": {"input": 3.0, "output": 15.0},
            "usage_unit": "tokens",
        },
        "claude-opus-4-8": {
            "context_window": 1_000_000,
            "cost_per_million": {"input": 5.0, "output": 25.0},
            "usage_unit": "tokens",
        },
    }

    def to_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Serialize messages to Anthropic format.

        Args:
            messages: List of Message objects

        Returns:
            List of message dicts in Anthropic format
        """
        result = []
        for msg in messages:
            if msg.role == "tool_result":
                # Tool results are user messages with special content structure
                result.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_use_id,
                        "content": msg.content
                    }]
                })
            else:
                # Regular user/assistant messages
                result.append({
                    "role": msg.role,
                    "content": msg.content
                })
        return result

    def to_tools(self, tools: Dict[str, Tool]) -> List[Dict[str, Any]]:
        """
        Serialize tools to Anthropic format.

        Args:
            tools: Dictionary of tool name -> Tool object

        Returns:
            List of tool dicts in Anthropic format
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": tool.parameters,
                    "required": list(tool.parameters.keys())
                }
            }
            for tool in tools.values()
        ]

    def to_payload(
        self, context: Context, max_output_tokens: int = 1024
    ) -> Dict[str, Any]:
        """
        Create the full Anthropic API request payload.

        Args:
            context: Context object with messages, tools, and system prompt
            max_output_tokens: Maximum tokens to generate

        Returns:
            Complete API request payload
        """
        return {
            "model": self._model,
            "system": context.system,
            "max_tokens": max_output_tokens,
            "tools": self.to_tools(context.tools),
            "messages": self.to_messages(context.messages)
        }

    @property
    def headers(self) -> Dict[str, str]:
        """Get HTTP headers for Anthropic API requests."""
        return {
            "Content-Type": "application/json",
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01"
        }

    @property
    def url(self) -> str:
        """Get the Anthropic API endpoint URL."""
        return self.BASE_URL
