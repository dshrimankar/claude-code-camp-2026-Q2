"""
Google Gemini API backend.

Serializes context into Google's Gemini API format.
https://ai.google.dev/api/generate-content
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List, Optional

from boukensha.backends.base import Base

if TYPE_CHECKING:
    from boukensha.context import Context
    from boukensha.message import Message
    from boukensha.tool import Tool


class Gemini(Base):
    """
    Backend for Google's Gemini API.

    Gemini has unique format requirements:
    - Uses "model" role instead of "assistant"
    - Content wrapped in parts array with text objects
    - Tool results use functionResponse format
    - Tools wrapped in functionDeclarations
    - System instruction has special format
    - URL includes model name
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    MODELS: Dict[str, Dict[str, Any]] = {
        "gemini-3.5-flash": {
            "context_window": 1_048_576,
            "cost_per_million": {"input": 1.5, "output": 9.0},
            "usage_unit": "tokens",
        },
        "gemini-3.1-flash-lite": {
            "context_window": 1_048_576,
            "cost_per_million": {"input": 0.25, "output": 1.5},
            "usage_unit": "tokens",
        },
        "gemini-2.5-pro": {
            "context_window": 1_048_576,
            "cost_per_million": {"input": 1.25, "output": 10.0},
            "usage_unit": "tokens",
        },
        "gemini-2.5-flash": {
            "context_window": 1_048_576,
            "cost_per_million": {"input": 0.30, "output": 2.50},
            "usage_unit": "tokens",
        },
        "gemini-2.5-flash-lite": {
            "context_window": 1_048_576,
            "cost_per_million": {"input": 0.10, "output": 0.40},
            "usage_unit": "tokens",
        },
    }

    def to_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Serialize messages to Gemini format.

        Gemini uses "model" instead of "assistant" and wraps
        content in parts arrays.

        Args:
            messages: List of Message objects

        Returns:
            List of message dicts in Gemini format
        """
        result = []
        for msg in messages:
            if msg.role == "assistant":
                # Gemini uses "model" instead of "assistant"
                if isinstance(msg.content, list):
                    # Assistant message with tool calls (normalized format)
                    # Need to rebuild Gemini's parts array
                    result.append({
                        "role": "model",
                        "parts": self._assistant_parts(msg.content)
                    })
                else:
                    result.append({
                        "role": "model",
                        "parts": [{"text": msg.content}]
                    })
            elif msg.role == "tool_result":
                # Tool results use functionResponse format
                result.append({
                    "role": "user",
                    "parts": [{
                        "functionResponse": {
                            "name": msg.tool_use_id,
                            "response": {"content": msg.content}
                        }
                    }]
                })
            else:
                # Regular user messages
                result.append({
                    "role": msg.role,
                    "parts": [{"text": msg.content}]
                })
        return result

    def to_tools(self, tools: Dict[str, Tool]) -> List[Dict[str, Any]]:
        """
        Serialize tools to Gemini format.

        Gemini wraps all tools in a single functionDeclarations array.

        Args:
            tools: Dictionary of tool name -> Tool object

        Returns:
            List with single dict containing functionDeclarations
        """
        if not tools:
            return []

        return [{
            "functionDeclarations": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": list(tool.parameters.keys())
                    }
                }
                for tool in tools.values()
            ]
        }]

    def to_payload(
        self,
        context: Context,
        max_output_tokens: int = 1024,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create the full Gemini API request payload.

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
            "systemInstruction": {
                "parts": [{"text": context.system}]
            },
            "contents": self.to_messages(context.messages),
            "tools": tools_value,
            "generationConfig": {
                "maxOutputTokens": max_output_tokens
            }
        }

    @property
    def headers(self) -> Dict[str, str]:
        """Get HTTP headers for Gemini API requests."""
        return {
            "Content-Type": "application/json",
            "x-goog-api-key": self._api_key
        }

    @property
    def url(self) -> str:
        """Get the Gemini API endpoint URL (includes model name)."""
        return f"{self.BASE_URL}/{self._model}:generateContent"

    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Gemini response into normalized format.

        Gemini uses candidates[0].content.parts array with functionCall objects.

        Args:
            response: Raw Gemini API response

        Returns:
            Normalized response with stop_reason and content
        """
        candidate = response.get("candidates", [{}])[0]
        content_obj = candidate.get("content", {})
        parts = content_obj.get("parts", [])

        content = []
        has_function_call = False

        for part in parts:
            if "text" in part:
                content.append({"type": "text", "text": part["text"]})
            elif "functionCall" in part:
                has_function_call = True
                fc = part["functionCall"]
                # Gemini uses function name as ID
                content.append({
                    "type": "tool_use",
                    "id": fc.get("name"),
                    "name": fc.get("name"),
                    "input": fc.get("args", {})
                })

        return {
            "stop_reason": "tool_use" if has_function_call else "end_turn",
            "content": content
        }

    def _assistant_parts(self, content: Any) -> List[Dict[str, Any]]:
        """
        Rebuild Gemini parts array from normalized content blocks.

        Converts normalized content blocks back to Gemini's parts format
        with text and functionCall objects.

        Args:
            content: String or list of content blocks

        Returns:
            List of Gemini-formatted parts
        """
        # Normalize to list
        if isinstance(content, str):
            blocks = [{"type": "text", "text": content}]
        else:
            blocks = content

        parts = []
        for block in blocks:
            if block.get("type") == "text":
                parts.append({"text": block.get("text", "")})
            elif block.get("type") == "tool_use":
                parts.append({
                    "functionCall": {
                        "name": block.get("name"),
                        "args": block.get("input", {})
                    }
                })

        return parts
