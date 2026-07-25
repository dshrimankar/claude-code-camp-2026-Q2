"""
Ollama local API backend.

Serializes context for local Ollama instances.
https://github.com/ollama/ollama/blob/main/docs/api.md
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List, Optional

from boukensha.backends.base import Base

if TYPE_CHECKING:
    from boukensha.context import Context
    from boukensha.message import Message
    from boukensha.tool import Tool


class Ollama(Base):
    """
    Backend for local Ollama instances.

    Ollama format is similar to OpenAI but:
    - Uses a host parameter instead of API key
    - Includes "stream: false" in payload
    - Tool results use "tool_name" instead of "tool_call_id"
    - Models have zero cost (local compute)
    """

    MODELS: Dict[str, Dict[str, Any]] = {
        "gemma4": {
            "context_window": 128_000,
            "cost_per_million": {"input": 0.0, "output": 0.0},
            "usage_unit": "local_compute",
        },
        "gemma4:e2b": {
            "context_window": 128_000,
            "cost_per_million": {"input": 0.0, "output": 0.0},
            "usage_unit": "local_compute",
        },
        "gemma4:e4b": {
            "context_window": 128_000,
            "cost_per_million": {"input": 0.0, "output": 0.0},
            "usage_unit": "local_compute",
        },
        "gemma4:12b": {
            "context_window": 256_000,
            "cost_per_million": {"input": 0.0, "output": 0.0},
            "usage_unit": "local_compute",
        },
        "gemma4:26b": {
            "context_window": 256_000,
            "cost_per_million": {"input": 0.0, "output": 0.0},
            "usage_unit": "local_compute",
        },
        "gemma4:31b": {
            "context_window": 256_000,
            "cost_per_million": {"input": 0.0, "output": 0.0},
            "usage_unit": "local_compute",
        },
        "qwen3:30b": {
            "context_window": 256_000,
            "cost_per_million": {"input": 0.0, "output": 0.0},
            "usage_unit": "local_compute",
        },
        "qwen3:8b": {
            "context_window": 40_000,
            "cost_per_million": {"input": 0.0, "output": 0.0},
            "usage_unit": "local_compute",
        },
        "deepseek-r1:8b": {
            "context_window": 128_000,
            "cost_per_million": {"input": 0.0, "output": 0.0},
            "usage_unit": "local_compute",
        },
    }

    def __init__(self, host: str = "http://localhost:11434", model: str = "") -> None:
        """
        Initialize the Ollama backend.

        Args:
            host: Ollama server host (default: http://localhost:11434)
            model: Model name to use
        """
        self._host = host
        # Call parent with dummy api_key since Ollama doesn't use it
        super().__init__(api_key="", model=model)

    def to_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Serialize messages to Ollama format.

        Note: This doesn't include the system message. Use the version
        that takes both system and messages for complete serialization.

        Args:
            messages: List of Message objects

        Returns:
            List of message dicts in Ollama format
        """
        return self._to_messages_with_system("", messages)[1:]  # Skip system message

    def _to_messages_with_system(
        self, system: str, messages: List[Message]
    ) -> List[Dict[str, Any]]:
        """
        Serialize system and messages to Ollama format.

        Ollama puts the system prompt in the messages array.

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
                # Ollama uses "tool_name" instead of "tool_call_id"
                conversation.append({
                    "role": "tool",
                    "tool_name": msg.tool_use_id,
                    "content": msg.content
                })
            elif msg.role == "assistant" and isinstance(msg.content, list):
                # Assistant message with tool calls (normalized format)
                # Need to rebuild Ollama's format with tool_calls array
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
        Serialize tools to Ollama format.

        Ollama uses the same format as OpenAI (function wrapper).

        Args:
            tools: Dictionary of tool name -> Tool object

        Returns:
            List of tool dicts in Ollama format
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
        Create the full Ollama API request payload.

        Args:
            context: Context object with messages, tools, and system prompt
            max_output_tokens: Maximum tokens to generate (ignored by Ollama)
            tools: Optional tools override (None uses context tools, [] disables tools)

        Returns:
            Complete API request payload
        """
        # Tools can be overridden (e.g., empty list to disable tools)
        tools_value = tools if tools is not None else self.to_tools(context.tools)

        return {
            "model": self._model,
            "stream": False,
            "messages": self._to_messages_with_system(
                context.system, context.messages
            ),
            "tools": tools_value
        }

    @property
    def headers(self) -> Dict[str, str]:
        """Get HTTP headers for Ollama API requests."""
        return {
            "Content-Type": "application/json"
        }

    @property
    def url(self) -> str:
        """Get the Ollama API endpoint URL."""
        return f"{self._host}/api/chat"

    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Ollama response into normalized format.

        Ollama uses message.tool_calls array. Unlike OpenAI/Anthropic,
        Ollama doesn't assign unique IDs - it reuses the function name as ID.

        Args:
            response: Raw Ollama API response

        Returns:
            Normalized response with stop_reason and content
        """
        message = response.get("message", {})
        tool_calls = message.get("tool_calls", [])

        content = []

        # Add text content if present
        text = message.get("content")
        if text:
            content.append({"type": "text", "text": text})

        # Add tool calls (Ollama uses function name as ID)
        for tc in tool_calls:
            fn = tc.get("function", {})
            content.append({
                "type": "tool_use",
                "id": fn.get("name"),  # Ollama uses name as ID
                "name": fn.get("name"),
                "input": fn.get("arguments", {})
            })

        return {
            "stop_reason": "tool_use" if tool_calls else "end_turn",
            "content": content
        }

    def _assistant_message(self, content: Any) -> Dict[str, Any]:
        """
        Rebuild Ollama assistant message from normalized content blocks.

        Converts normalized content blocks back to Ollama's format
        with tool_calls array.

        Args:
            content: String or list of content blocks

        Returns:
            Ollama-formatted assistant message
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
                    "function": {
                        "name": b.get("name"),
                        "arguments": b.get("input", {})
                    }
                }
                for b in tool_blocks
            ]

        return message
