"""
OpenAI GPT API backend.

Serializes context into OpenAI's Chat Completions API format.
https://platform.openai.com/docs/api-reference/chat/create
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List, Optional

from boukensha.backends.base import Base

if TYPE_CHECKING:
    from boukensha.context import Context
    from boukensha.message import Message
    from boukensha.tool import Tool


class OpenAI(Base):
    """
    Backend for OpenAI's GPT API.

    OpenAI has specific format requirements:
    - System prompt goes in the messages array as first message
    - Tools are wrapped in {type: "function", function: {...}}
    - Tool results use "tool" role with "tool_call_id"
    - Uses "max_completion_tokens" instead of "max_tokens"
    """

    BASE_URL = "https://api.openai.com/v1/chat/completions"

    MODELS: Dict[str, Dict[str, Any]] = {
        "gpt-5.5": {
            "context_window": 1_000_000,
            "cost_per_million": {"input": 5.0, "output": 30.0},
            "usage_unit": "tokens",
        },
        "gpt-5.4": {
            "context_window": 1_000_000,
            "cost_per_million": {"input": 2.5, "output": 15.0},
            "usage_unit": "tokens",
        },
        "gpt-5.4-mini": {
            "context_window": 400_000,
            "cost_per_million": {"input": 0.75, "output": 4.5},
            "usage_unit": "tokens",
        },
    }

    def to_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Serialize messages to OpenAI format.

        Note: This doesn't include the system message. Use the version
        that takes both system and messages for complete serialization.

        Args:
            messages: List of Message objects

        Returns:
            List of message dicts in OpenAI format
        """
        return self._to_messages_with_system("", messages)[1:]  # Skip system message

    def _to_messages_with_system(
        self, system: str, messages: List[Message]
    ) -> List[Dict[str, Any]]:
        """
        Serialize system and messages to OpenAI format.

        OpenAI puts the system prompt in the messages array.

        Args:
            system: System prompt
            messages: List of Message objects

        Returns:
            List of message dicts with system first
        """
        system_message = [{"role": "system", "content": system}]
        conversation = []

        for msg in messages:
            if msg.role == "tool_result":
                # OpenAI uses "tool" role with "tool_call_id"
                conversation.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_use_id,
                    "content": msg.content
                })
            elif msg.role == "assistant" and isinstance(msg.content, list):
                # Assistant message with tool calls (normalized format)
                # Need to rebuild OpenAI's format with tool_calls array
                conversation.append(self._assistant_message(msg.content))
            else:
                # Regular user/assistant messages with string content
                conversation.append({
                    "role": msg.role,
                    "content": msg.content
                })

        return system_message + conversation

    def to_tools(self, tools: Dict[str, Tool]) -> List[Dict[str, Any]]:
        """
        Serialize tools to OpenAI format.

        OpenAI wraps tools in a "function" object.

        Args:
            tools: Dictionary of tool name -> Tool object

        Returns:
            List of tool dicts in OpenAI format
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": list(tool.parameters.keys())
                    }
                }
            }
            for tool in tools.values()
        ]

    def to_payload(
        self,
        context: Context,
        max_output_tokens: int = 1024,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create the full OpenAI API request payload.

        Args:
            context: Context object with messages, tools, and system prompt
            max_output_tokens: Maximum tokens to generate
            tools: Optional tools override (None uses context tools, [] disables tools)

        Returns:
            Complete API request payload
        """
        # Tools can be overridden (e.g., empty list to disable tools)
        tools_value = tools if tools is not None else self.to_tools(context.tools)

        return {
            "model": self._model,
            "messages": self._to_messages_with_system(
                context.system, context.messages
            ),
            "tools": tools_value,
            "max_completion_tokens": max_output_tokens
        }

    @property
    def headers(self) -> Dict[str, str]:
        """Get HTTP headers for OpenAI API requests."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}"
        }

    @property
    def url(self) -> str:
        """Get the OpenAI API endpoint URL."""
        return self.BASE_URL

    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse OpenAI response into normalized format.

        OpenAI uses choices[0].message with optional tool_calls array.

        Args:
            response: Raw OpenAI API response

        Returns:
            Normalized response with stop_reason and content
        """
        message = response.get("choices", [{}])[0].get("message", {})
        tool_calls = message.get("tool_calls", [])

        content = []

        # Add text content if present
        text = message.get("content")
        if text:
            content.append({"type": "text", "text": text})

        # Add tool calls
        for tc in tool_calls:
            fn = tc.get("function", {})
            content.append({
                "type": "tool_use",
                "id": tc.get("id"),
                "name": fn.get("name"),
                "input": fn.get("arguments", {})
            })

        return {
            "stop_reason": "tool_use" if tool_calls else "end_turn",
            "content": content
        }

    def _assistant_message(self, content: Any) -> Dict[str, Any]:
        """
        Rebuild OpenAI assistant message from normalized content blocks.

        Converts normalized content blocks back to OpenAI's format
        with tool_calls array.

        Args:
            content: String or list of content blocks

        Returns:
            OpenAI-formatted assistant message
        """
        # Normalize to list
        if isinstance(content, str):
            blocks = [{"type": "text", "text": content}]
        else:
            blocks = content

        # Extract text and tool blocks
        text_blocks = [b for b in blocks if b.get("type") == "text"]
        tool_blocks = [b for b in blocks if b.get("type") == "tool_use"]

        # Build message
        message: Dict[str, Any] = {
            "role": "assistant",
            "content": "".join(b.get("text", "") for b in text_blocks)
        }

        # Add tool_calls if present
        if tool_blocks:
            message["tool_calls"] = [
                {
                    "id": b.get("id"),
                    "type": "function",
                    "function": {
                        "name": b.get("name"),
                        "arguments": b.get("input", {})
                    }
                }
                for b in tool_blocks
            ]

        return message
