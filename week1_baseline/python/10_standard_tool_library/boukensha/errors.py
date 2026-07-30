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


class ApiError(Exception):
    """
    Raised when an API request to an LLM provider fails.

    This error indicates the HTTP request to the LLM provider failed
    after all retry attempts. Common causes include:

    - Invalid or expired API key (401 Unauthorized, 403 Forbidden)
    - Rate limiting exceeded (429 Too Many Requests)
    - Server errors (500, 502, 503, 504)
    - Network connectivity issues
    - Malformed request payload (400 Bad Request)
    - Service unavailable or down

    The error message includes the HTTP status code (if available) and
    the response body or error details.

    Example:
        >>> client = Client(builder)
        >>> response = client.call()
        ApiError: API request failed after 3 attempts (429): Rate limit exceeded.
        Please retry after 60 seconds.

    Note:
        The Client automatically retries on transient failures (408, 429,
        500, 502, 503, 504) with exponential backoff. If ApiError is raised,
        all retry attempts have been exhausted.
    """

    pass


class LoopError(Exception):
    """
    Raised when the agent loop encounters an error.

    This error indicates something went wrong during the agent loop
    execution, such as malformed responses or unexpected states.

    Example:
        >>> agent = Agent(...)
        >>> result = agent.run()
        LoopError: Unexpected response format from provider
    """

    pass


class CollisionError(Exception):
    """
    Raised when MCP tool names collide.

    This error indicates two MCP tools are trying to register with the same
    name. This is always fatal, even for optional servers, because it represents
    a configuration contradiction that must be resolved.

    Resolution: Give one of the conflicting servers a distinct `prefix:` in
    the mcp_servers configuration.

    Example:
        >>> from boukensha.tools import mcp
        >>> mcp.register(registry, command="server1", prefix=None)
        >>> mcp.register(registry, command="server2", prefix=None)
        CollisionError: MCP tool name collision on 'look' — a tool by that
        name is already registered. Give this server a distinct `prefix:`
        in mcp_servers.
    """

    pass
