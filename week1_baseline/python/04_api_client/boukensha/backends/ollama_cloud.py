"""
Ollama Cloud API backend.

Serializes context for Ollama's cloud service.
https://ollama.com/
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List, Optional

from boukensha.backends.base import Base

if TYPE_CHECKING:
    from boukensha.context import Context
    from boukensha.message import Message
    from boukensha.tool import Tool


class OllamaCloud(Base):
    """
    Backend for Ollama Cloud service.

    OllamaCloud format is similar to local Ollama but:
    - Requires API key authentication
    - Uses https://ollama.com base URL
    - Models may have usage levels but no explicit pricing
    """

    BASE_URL = "https://ollama.com"

    MODELS: Dict[str, Dict[str, Any]] = {
        "gemma4:31b-cloud": {
            "context_window": 256_000,
            "cost_per_million": {"input": None, "output": None},
            "usage_unit": "ollama_cloud_usage",
            "usage_level": "medium",
        },
        "minimax-m3:cloud": {
            "context_window": 512_000,
            "advertised_context_window": 1_000_000,
            "cost_per_million": {"input": None, "output": None},
            "usage_unit": "ollama_cloud_usage",
            "usage_level": "high",
        },
        "kimi-k2.5:cloud": {
            "context_window": 256_000,
            "cost_per_million": {"input": None, "output": None},
            "usage_unit": "ollama_cloud_usage",
            "usage_level": "high",
        },
    }

    def to_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Serialize messages to OllamaCloud format.

        Note: This doesn't include the system message. Use the version
        that takes both system and messages for complete serialization.

        Args:
            messages: List of Message objects

        Returns:
            List of message dicts in OllamaCloud format
        """
        return self._to_messages_with_system("", messages)[1:]  # Skip system message

    def _to_messages_with_system(
        self, system: str, messages: List[Message]
    ) -> List[Dict[str, Any]]:
        """
        Serialize system and messages to OllamaCloud format.

        OllamaCloud puts the system prompt in the messages array.

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
                # OllamaCloud uses "tool_name" instead of "tool_call_id"
                conversation.append({
                    "role": "tool",
                    "tool_name": msg.tool_use_id,
                    "content": msg.content
                })
            else:
                # Regular user/assistant messages
                conversation.append({
                    "role": msg.role,
                    "content": msg.content
                })

        return system_message + conversation

    def to_tools(self, tools: Dict[str, Tool]) -> List[Dict[str, Any]]:
        """
        Serialize tools to OllamaCloud format.

        OllamaCloud uses the same format as OpenAI (function wrapper).

        Args:
            tools: Dictionary of tool name -> Tool object

        Returns:
            List of tool dicts in OllamaCloud format
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
        self, context: Context, max_output_tokens: int = 1024
    ) -> Dict[str, Any]:
        """
        Create the full OllamaCloud API request payload.

        Args:
            context: Context object with messages, tools, and system prompt
            max_output_tokens: Maximum tokens to generate (ignored)

        Returns:
            Complete API request payload
        """
        return {
            "model": self._model,
            "stream": False,
            "messages": self._to_messages_with_system(
                context.system, context.messages
            ),
            "tools": self.to_tools(context.tools)
        }

    @property
    def headers(self) -> Dict[str, str]:
        """Get HTTP headers for OllamaCloud API requests."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}"
        }

    @property
    def url(self) -> str:
        """Get the OllamaCloud API endpoint URL."""
        return f"{self.BASE_URL}/api/chat"

    def estimate_cost(
        self, input_tokens: int, output_tokens: int
    ) -> Optional[float]:
        """
        Estimate cost (always None for OllamaCloud without pricing).

        OllamaCloud doesn't publish explicit pricing, so cost estimation
        is not available.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            None (pricing not available)
        """
        return None
