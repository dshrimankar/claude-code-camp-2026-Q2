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
