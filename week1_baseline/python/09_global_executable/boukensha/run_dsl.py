from typing import Dict, Callable, Any, Optional


class RunDSL:
    """DSL surface object for Boukensha.run() blocks.

    Exposes only the tool() method to keep the DSL surface intentionally small.
    """

    def __init__(self, registry):
        """Initialize with a Registry instance."""
        self._registry = registry

    def tool(
        self,
        name: str,
        *,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        implementation: Callable[..., Any]
    ) -> None:
        """Register a tool with the agent.

        Args:
            name: Tool name (e.g., "read_file")
            description: What the tool does
            parameters: JSON schema for tool parameters
            implementation: Callable that executes the tool
        """
        if parameters is None:
            parameters = {}
        self._registry.tool(
            name,
            description=description,
            parameters=parameters,
            block=implementation
        )
