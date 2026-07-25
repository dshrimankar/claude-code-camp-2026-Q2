"""Custom exceptions for Boukensha."""


class UnknownToolError(Exception):
    """
    Raised when attempting to dispatch a tool that doesn't exist.

    This error indicates the agent requested a tool that was never
    registered with the Registry. This typically means:
    - The tool name was misspelled
    - The tool wasn't registered before dispatch
    - The agent hallucinated a tool that doesn't exist

    Example:
        >>> registry.dispatch("nonexistent_tool")
        UnknownToolError: No tool registered as 'nonexistent_tool'
    """

    pass


class UnsupportedModelError(Exception):
    """
    Raised when attempting to use an unsupported model with a backend.

    This error indicates the specified model is not available for the
    selected backend provider. Each backend has a specific set of
    supported models defined in its MODELS catalog.

    Example:
        >>> backend = AnthropicBackend(api_key="key", model="gpt-4")
        UnsupportedModelError: Anthropic does not support model 'gpt-4'.
        Supported models: claude-haiku-4-5, claude-sonnet-4-6, ...
    """

    pass
