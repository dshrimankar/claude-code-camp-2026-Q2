"""
Prompt builder facade for LLM API integration.

The PromptBuilder acts as a facade that delegates to provider-specific
backends for serialization. This allows the agent logic to remain
provider-agnostic while supporting multiple LLM APIs.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List

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

    def to_api_payload(self, max_output_tokens: int = 1024) -> Dict[str, Any]:
        """
        Create the complete API request payload.

        Args:
            max_output_tokens: Maximum tokens to generate (default: 1024)

        Returns:
            Complete API request payload as a dict
        """
        return self._backend.to_payload(
            self._context, max_output_tokens=max_output_tokens
        )

    @property
    def headers(self) -> Dict[str, str]:
        """Get the HTTP headers for API requests."""
        return self._backend.headers

    @property
    def url(self) -> str:
        """Get the API endpoint URL."""
        return self._backend.url

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
