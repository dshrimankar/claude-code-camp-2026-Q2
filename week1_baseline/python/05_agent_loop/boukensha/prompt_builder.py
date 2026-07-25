"""
Prompt builder facade for LLM API integration.

The PromptBuilder acts as a facade that delegates to provider-specific
backends for serialization. This allows the agent logic to remain
provider-agnostic while supporting multiple LLM APIs.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List, Optional

if TYPE_CHECKING:
    from boukensha.context import Context
    from boukensha.backends.base import Base


class PromptBuilder:
    """
    Facade for building LLM API requests from context.

    The PromptBuilder delegates to a backend to serialize the context
    into the provider-specific API format. This provides a uniform
    interface for the agent while supporting multiple providers.

    Example:
        >>> from boukensha import Context
        >>> from boukensha.backends.anthropic import Anthropic
        >>>
        >>> ctx = Context(...)
        >>> backend = Anthropic(api_key="sk-...", model="claude-sonnet-4-6")
        >>> builder = PromptBuilder(context=ctx, backend=backend)
        >>>
        >>> payload = builder.to_api_payload(max_output_tokens=2048)
        >>> # Make API request with payload, builder.headers, builder.url
    """

    def __init__(self, context: Context, backend: Base) -> None:
        """
        Initialize the prompt builder.

        Args:
            context: Context object with messages, tools, and system prompt
            backend: Backend instance for provider-specific serialization
        """
        self._context = context
        self._backend = backend

    @property
    def context(self) -> Context:
        """Get the context object."""
        return self._context

    @property
    def backend(self) -> Base:
        """Get the backend instance."""
        return self._backend

    def to_messages(self) -> List[Dict[str, Any]]:
        """
        Serialize messages to provider format.

        Returns:
            List of message dicts in provider-specific format
        """
        return self._backend.to_messages(self._context.messages)

    def to_tools(self) -> List[Dict[str, Any]]:
        """
        Serialize tools to provider format.

        Returns:
            List of tool dicts in provider-specific format
        """
        return self._backend.to_tools(self._context.tools)

    def to_api_payload(
        self,
        max_output_tokens: int = 1024,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create the complete API request payload.

        Args:
            max_output_tokens: Maximum tokens to generate (default: 1024)
            tools: Optional tools override (None uses context tools, [] disables tools)

        Returns:
            Complete API request payload as a dict
        """
        return self._backend.to_payload(
            self._context, max_output_tokens=max_output_tokens, tools=tools
        )

    @property
    def headers(self) -> Dict[str, str]:
        """Get the HTTP headers for API requests."""
        return self._backend.headers

    @property
    def url(self) -> str:
        """Get the API endpoint URL."""
        return self._backend.url

    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse provider response into normalized format.

        Delegates to the backend to convert the provider-specific response
        format into a common normalized shape with stop_reason and content.

        Args:
            response: Raw API response from the provider

        Returns:
            Normalized response dict with:
            - stop_reason: "tool_use" or "end_turn"
            - content: List of content blocks (text and/or tool_use)
        """
        return self._backend.parse_response(response)

    def __repr__(self) -> str:
        """Get a debug representation of the prompt builder."""
        backend_name = self._backend.__class__.__name__
        model = self._backend.model
        tool_count = len(self._context.tools)
        msg_count = len(self._context.messages)
        return (
            f"#<PromptBuilder backend={backend_name} "
            f"model={model} tools={tool_count} messages={msg_count}>"
        )
