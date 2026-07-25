"""
Abstract base class for LLM provider backends.

Each backend is responsible for:
- Maintaining a catalog of supported models with metadata
- Validating model names
- Serializing context into provider-specific API formats
- Providing cost estimation for token usage
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Any, List, Optional

if TYPE_CHECKING:
    from boukensha.context import Context
    from boukensha.message import Message
    from boukensha.tool import Tool

from boukensha.errors import UnsupportedModelError


class Base(ABC):
    """
    Abstract base class for LLM provider backends.

    Each backend must:
    1. Define a MODELS class variable with model metadata
    2. Implement to_messages() to serialize messages
    3. Implement to_tools() to serialize tools
    4. Implement to_payload() to create the full API request
    5. Implement headers property for API headers
    6. Implement url property for API endpoint
    """

    # Subclasses must override this with their model catalog
    MODELS: Dict[str, Dict[str, Any]] = {}

    def __init__(self, api_key: str, model: str) -> None:
        """
        Initialize the backend with API credentials and model selection.

        Args:
            api_key: API key for the provider
            model: Model name to use (must be in MODELS catalog)

        Raises:
            UnsupportedModelError: If model is not supported by this backend
        """
        self._api_key = api_key
        self._configure_model(model)

    @classmethod
    def models(cls) -> Dict[str, Dict[str, Any]]:
        """Get the models catalog for this backend."""
        if not hasattr(cls, 'MODELS'):
            raise NotImplementedError(f"{cls.__name__} must define MODELS")
        return cls.MODELS

    @classmethod
    def model_info(cls, model: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific model."""
        return cls.models().get(model)

    @classmethod
    def validate_model(cls, model: str) -> str:
        """
        Validate that a model is supported by this backend.

        Args:
            model: Model name to validate

        Returns:
            The validated model name

        Raises:
            UnsupportedModelError: If model is not supported
        """
        if cls.model_info(model) is not None:
            return model

        supported = ", ".join(sorted(cls.models().keys()))
        raise UnsupportedModelError(
            f"{cls.__name__} does not support model {model!r}. "
            f"Supported models: {supported}"
        )

    @property
    def model(self) -> str:
        """Get the current model name."""
        return self._model

    @property
    def model_info_dict(self) -> Dict[str, Any]:
        """Get metadata for the current model."""
        return self._model_info

    @property
    def context_window(self) -> int:
        """Get the context window size for the current model."""
        return self._model_info["context_window"]

    @property
    def input_token_cost_per_million(self) -> float:
        """Get the input token cost per million tokens."""
        return self._model_info["cost_per_million"]["input"]

    @property
    def output_token_cost_per_million(self) -> float:
        """Get the output token cost per million tokens."""
        return self._model_info["cost_per_million"]["output"]

    @property
    def usage_unit(self) -> str:
        """Get the usage unit (e.g., 'tokens', 'characters')."""
        return self._model_info["usage_unit"]

    @property
    def usage_level(self) -> Optional[str]:
        """Get the usage level if defined (e.g., 'tier1', 'tier2')."""
        return self._model_info.get("usage_level")

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> Optional[float]:
        """
        Estimate the cost of a request in USD.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD, or None if pricing unavailable
        """
        try:
            input_cost = input_tokens * self.input_token_cost_per_million
            output_cost = output_tokens * self.output_token_cost_per_million
            return (input_cost + output_cost) / 1_000_000.0
        except (KeyError, TypeError):
            return None

    @abstractmethod
    def to_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Serialize messages to provider-specific format.

        Args:
            messages: List of Message objects

        Returns:
            List of message dicts in provider format
        """
        ...

    @abstractmethod
    def to_tools(self, tools: Dict[str, Tool]) -> List[Dict[str, Any]]:
        """
        Serialize tools to provider-specific format.

        Args:
            tools: Dictionary of tool name -> Tool object

        Returns:
            List of tool dicts in provider format
        """
        ...

    @abstractmethod
    def to_payload(
        self, context: Context, max_output_tokens: int = 1024
    ) -> Dict[str, Any]:
        """
        Create the full API request payload.

        Args:
            context: Context object with messages, tools, and system prompt
            max_output_tokens: Maximum tokens to generate

        Returns:
            Complete API request payload as a dict
        """
        ...

    @property
    @abstractmethod
    def headers(self) -> Dict[str, str]:
        """Get the HTTP headers for API requests."""
        ...

    @property
    @abstractmethod
    def url(self) -> str:
        """Get the API endpoint URL."""
        ...

    def _configure_model(self, model: str) -> None:
        """
        Validate and configure the model.

        Args:
            model: Model name to configure

        Raises:
            UnsupportedModelError: If model is not supported
        """
        self._model = self.validate_model(model)
        self._model_info = self.model_info(self._model) or {}
