from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from boukensha.context import Context
from boukensha.errors import UnknownToolError
from boukensha.tool import Tool


class Registry:
    """
    Central tool registry for registration and dispatch.

    The Registry manages tool registration and routes tool execution
    requests. The agent never calls tools directly; instead it emits
    structured requests (name + args) that the Registry dispatches.

    This simulates how real LLM agents work: the model outputs JSON
    tool use requests, and the harness looks up and executes the tool.

    Attributes:
        context: The Context that stores registered tools
    """

    def __init__(self, context: Context) -> None:
        """
        Initialize a new registry.

        Args:
            context: Context to store registered tools in
        """
        self._context = context

    def tool(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        block: Optional[Callable[..., Any]] = None,
    ) -> None:
        """
        Register a tool with the registry.

        This is a convenience method that creates a Tool object and
        registers it with the context. The tool becomes available for
        dispatch via the registry.

        Args:
            name: Unique tool identifier
            description: Human-readable description for the agent
            parameters: JSON schema for tool parameters (defaults to {})
            block: Callable to execute when tool is invoked

        Raises:
            ValueError: If block is None (tool must have implementation)

        Example:
            >>> def move_fn(direction: str) -> str:
            ...     return f"Moving {direction}"
            >>> registry.tool(
            ...     name="move",
            ...     description="Move the player",
            ...     parameters={"direction": {"type": "string"}},
            ...     block=move_fn
            ... )
        """
        if parameters is None:
            parameters = {}

        if block is None:
            raise ValueError("Tool must have a callable block")

        t = Tool(
            name=name,
            description=description,
            parameters=parameters,
            block=block,
        )
        self._context.register_tool(t)

    def dispatch(self, name: str, args: Optional[Dict[str, Any]] = None) -> Any:
        """
        Dispatch a tool call by name with arguments.

        Looks up the tool in the context and executes it with the
        provided arguments. This is the primary method for executing
        tools - the agent never calls tools directly.

        Args:
            name: Name of the tool to execute
            args: Arguments to pass to the tool (defaults to {})

        Returns:
            The result of executing the tool

        Raises:
            UnknownToolError: If no tool with the given name exists

        Example:
            >>> result = registry.dispatch("move", {"direction": "north"})
            >>> print(result)
            Moving north
        """
        if args is None:
            args = {}

        tool = self._context.tools.get(name)

        if tool is None:
            raise UnknownToolError(f"No tool registered as '{name}'")

        # Execute the tool's block with the arguments
        # Note: Python doesn't need symbol key transformation like Ruby
        # String keys work directly with keyword argument unpacking
        return tool.block(**args)
