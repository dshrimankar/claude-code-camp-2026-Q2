"""
The agent loop - sends requests, dispatches tools, and knows when to stop.

The Agent implements the core loop pattern:
1. Send messages to the API
2. Check if stop_reason is "tool_use"
3. If yes: extract tool calls, dispatch them, inject results, loop
4. If no: return final text response
5. Enforce max_iterations limit with graceful wind-down
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List, Optional

if TYPE_CHECKING:
    from boukensha.context import Context
    from boukensha.registry import Registry
    from boukensha.prompt_builder import PromptBuilder
    from boukensha.client import Client

from boukensha.errors import ApiError


class Agent:
    """
    The agent loop - sends requests, dispatches tools, and knows when to stop.

    The Agent:
    1. Sends messages to the API
    2. Checks if stop_reason is "tool_use"
    3. If yes: extracts tool calls, dispatches them, injects results, loops
    4. If no: returns final text response
    5. Enforces max_iterations limit with graceful wind-down

    Example:
        >>> agent = Agent(
        ...     context=ctx,
        ...     registry=registry,
        ...     builder=builder,
        ...     client=client
        ... )
        >>> result = agent.run()
        >>> print(result)
    """

    # Default iteration ceiling
    MAX_ITERATIONS = 25

    # Wind-down call settings
    WRAP_UP_OUTPUT_TOKENS = 400
    WRAP_UP_DIRECTIVE = (
        "You have reached your action limit for this turn. Do not call any more tools. "
        "Briefly summarize what you accomplished, what is still unfinished, and the "
        "single next action you would take."
    )

    def __init__(
        self,
        context: Context,
        registry: Registry,
        builder: PromptBuilder,
        client: Client,
        task_settings: Optional[Dict[str, Any]] = None,
        max_iterations: Optional[int] = None,
        max_output_tokens: Optional[int] = None,
    ) -> None:
        """
        Initialize the agent.

        Args:
            context: Context object with messages, tools, and system prompt
            registry: Registry for tool dispatch
            builder: PromptBuilder for API serialization
            client: Client for API requests
            task_settings: Optional task settings dictionary
            max_iterations: Optional explicit max iterations (overrides settings)
            max_output_tokens: Optional explicit max output tokens (overrides settings)
        """
        self._context = context
        self._registry = registry
        self._builder = builder
        self._client = client
        self._max_iterations = self._resolve_max_iterations(task_settings, max_iterations)
        self._max_output_tokens = self._resolve_max_output_tokens(task_settings, max_output_tokens)
        self._iteration = 0

    def run(self) -> str:
        """
        Run the agent loop until completion.

        The loop continues until either:
        - The model returns end_turn (no more tool calls)
        - The iteration limit is reached (triggers wind-down)

        Returns:
            Final text response from the agent
        """
        while True:
            # Check iteration limit
            if self._iteration_limit_reached():
                return self._wrap_up("max_iterations")

            self._iteration += 1
            print(f"[iteration {self._iteration}/{self._max_iterations}]")

            # Make API call
            response = self._client.call(**self._call_opts())
            parsed = self._builder.parse_response(response)

            # Check stop reason
            if parsed["stop_reason"] == "tool_use":
                self._handle_tool_calls(parsed["content"])
            else:
                return self._extract_text(parsed["content"])

    def _handle_tool_calls(self, content: List[Dict[str, Any]]) -> None:
        """
        Handle tool use blocks by dispatching and injecting results.

        Args:
            content: List of content blocks from normalized response
        """
        # Add assistant message with tool use blocks
        self._context.add_message("assistant", content)

        # Dispatch each tool call
        for block in content:
            if block.get("type") == "tool_use":
                name = block["name"]
                args = block["input"]
                use_id = block["id"]

                print(f"  tool call → {name}({args})")
                result = self._registry.dispatch(name, args)
                print(f"  tool result → {str(result)[:60]}")

                self._context.add_message("tool_result", str(result), tool_use_id=use_id)

    def _extract_text(self, content: List[Dict[str, Any]]) -> str:
        """
        Extract text from content blocks.

        Args:
            content: List of content blocks

        Returns:
            Concatenated text from all text blocks
        """
        return "".join(block.get("text", "") for block in content if block.get("type") == "text")

    def _wrap_up(self, reason: str) -> str:
        """
        Make a final wind-down call without tools.

        When the iteration limit is reached, this method makes one final
        API call with tools disabled to get a summary from the model.

        Args:
            reason: Reason for wrap-up (e.g., "max_iterations")

        Returns:
            Wind-down response or fallback message
        """
        self._context.add_message("user", self.WRAP_UP_DIRECTIVE)

        try:
            response = self._client.call(tools=[], max_output_tokens=self.WRAP_UP_OUTPUT_TOKENS)
            text = self._extract_text(self._builder.parse_response(response)["content"])
            return text if text.strip() else self._fallback_message(reason)
        except ApiError:
            return self._fallback_message(reason)

    def _fallback_message(self, reason: str) -> str:
        """
        Return a fallback message when wind-down fails.

        Args:
            reason: Reason for fallback

        Returns:
            Fallback message string
        """
        return (
            f"I reached my {self._max_iterations}-action limit for this turn before finishing "
            f"({reason}). Ask me to continue and I'll pick up from here."
        )

    def _iteration_limit_reached(self) -> bool:
        """
        Check if iteration limit has been reached.

        Returns:
            True if iteration limit reached, False otherwise
        """
        return self._max_iterations > 0 and self._iteration >= self._max_iterations

    def _call_opts(self) -> Dict[str, Any]:
        """
        Get call options for API requests.

        Returns:
            Dictionary of call options
        """
        return {"max_output_tokens": self._max_output_tokens} if self._max_output_tokens else {}

    def _resolve_max_iterations(
        self, task_settings: Optional[Dict[str, Any]], explicit: Optional[int]
    ) -> int:
        """
        Resolve max_iterations from settings or explicit value.

        Args:
            task_settings: Optional task settings dictionary
            explicit: Optional explicit max iterations value

        Returns:
            Resolved max iterations value
        """
        if explicit is not None:
            return int(explicit)
        if task_settings and hasattr(self._context.task, 'max_iterations'):
            return self._context.task.max_iterations(task_settings)
        return self.MAX_ITERATIONS

    def _resolve_max_output_tokens(
        self, task_settings: Optional[Dict[str, Any]], explicit: Optional[int]
    ) -> Optional[int]:
        """
        Resolve max_output_tokens from settings or explicit value.

        Args:
            task_settings: Optional task settings dictionary
            explicit: Optional explicit max output tokens value

        Returns:
            Resolved max output tokens value or None
        """
        if explicit is not None:
            return explicit
        if task_settings and hasattr(self._context.task, 'max_output_tokens'):
            return self._context.task.max_output_tokens(task_settings)
        return None

    def __repr__(self) -> str:
        """Get a debug representation of the agent."""
        return (
            f"#<Agent iteration={self._iteration}/{self._max_iterations} "
            f"messages={len(self._context.messages)}>"
        )
