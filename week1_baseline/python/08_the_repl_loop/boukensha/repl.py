"""
Interactive REPL (Read-Eval-Print Loop) for Boukensha.

The Repl class wraps the same primitives as Boukensha.run(), but stays alive
in a loop instead of running once. It reads user input, runs the agent, prints
the response, and repeats.

Context is shared across turns so conversation history accumulates naturally.
"""

from pathlib import Path
from typing import Optional

import boukensha
from boukensha.agent import Agent
from boukensha.errors import LoopError, ApiError


class Repl:
    """
    Interactive REPL session loop.

    The Repl wraps the same primitives as a single Boukensha.run call, but
    instead of running once it stays alive: it reads a task from the user,
    runs the agent, prints the reply, and loops back to the prompt.

    The Context is shared across every turn so conversation history accumulates
    naturally — the agent sees the full transcript each time it is called.

    Built-in commands (not sent to the agent):
        /help    print the command list
        /quiet   suppress detailed logging
        /loud    re-enable logging
        /clear   wipe conversation history (tools stay registered)
        /exit    leave the REPL
        /quit    alias for /exit
    """

    PROMPT = "boukensha> "

    HELP = """Commands:
  /quiet   suppress logging output
  /loud    re-enable logging output
  /clear   wipe conversation history (tools stay)
  /exit    leave the REPL
  /help    show this message
"""

    def __init__(
        self,
        *,
        context,
        registry,
        builder,
        client,
        logger,
        config_dir: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        version: Optional[str] = None,
        api_key: Optional[str] = None,
        task_settings: Optional[dict] = None,
        max_iterations: Optional[int] = None,
        max_output_tokens: Optional[int] = None
    ):
        """
        Initialize REPL with all required components.

        Args:
            context: Context instance
            registry: Registry instance
            builder: PromptBuilder instance
            client: Client instance
            logger: Logger instance
            config_dir: Optional config directory path
            provider: Optional provider name
            model: Optional model name
            version: Optional version string
            api_key: Optional API key
            task_settings: Optional task settings dict
            max_iterations: Optional max iterations
            max_output_tokens: Optional max output tokens
        """
        self._context = context
        self._registry = registry
        self._builder = builder
        self._client = client
        self._logger = logger
        self._task_settings = task_settings
        self._max_iterations = max_iterations
        self._max_output_tokens = max_output_tokens
        self._config_dir = config_dir
        self._provider = provider
        self._model = model
        self._version = version
        self._api_key = api_key
        self._turn = 0

    def start(self) -> None:
        """Start the interactive REPL loop."""
        print(self._banner())

        while True:
            try:
                user_input = input(self.PROMPT).strip()
                if not user_input:
                    continue

                # Handle built-in commands
                if user_input in ("/exit", "/quit"):
                    print("Goodbye.")
                    break
                elif user_input == "/help":
                    print(self.HELP)
                    continue
                elif user_input == "/quiet":
                    boukensha.quiet()
                    print("(logging suppressed — type /loud to re-enable)")
                    continue
                elif user_input == "/loud":
                    boukensha.loud()
                    print("(logging enabled)")
                    continue
                elif user_input == "/clear":
                    self._context.clear_messages()
                    self._turn = 0
                    print("(conversation history cleared)")
                    continue

                # Run agent turn
                self._run_turn(user_input)

            except EOFError:  # Ctrl-D / EOF
                break
            except KeyboardInterrupt:  # Ctrl-C
                print("\nInterrupted.")
                break

    def _banner(self) -> str:
        """Generate the startup banner."""
        # API key status
        key_status = "✗ API key not set" if (not self._api_key or not self._api_key.strip()) else "✓ API key set"
        provider_line = f"{self._provider or 'default'} ({self._model or 'default'})  {key_status}"

        # Config directory status
        config_exists = self._config_dir and Path(self._config_dir).exists()
        config_line = self._config_dir if config_exists else f"{self._config_dir or '(default)'}  ✗ directory not found"

        # Version
        ver = self._version or "?.?.?"
        padding = " " * (9 - len(ver))

        return f"""
╔══════════════════════════════════════╗
║  BOUKENSHA MUD Assistant (v{ver}){padding}║
╚══════════════════════════════════════╝
  config:    {config_line}
  provider:  {provider_line}

  /quiet or /loud   toggle logging
  /clear           reset conversation history
  /exit or /quit    leave the REPL

"""

    def _run_turn(self, user_input: str) -> None:
        """
        Execute one REPL turn with error handling.

        Args:
            user_input: User's input string
        """
        self._turn += 1
        self._logger.turn(n=self._turn)

        self._context.add_message("user", user_input)

        agent = Agent(
            context=self._context,
            registry=self._registry,
            builder=self._builder,
            client=self._client,
            logger=self._logger,
            task_settings=self._task_settings,
            max_iterations=self._max_iterations,
            max_output_tokens=self._max_output_tokens,
        )

        try:
            result = agent.run()

            # Print the final response outside of the logger so it is always visible,
            # even when boukensha.quiet() is active.
            print()
            print(result)
        except LoopError as e:
            print(f"\n[error] {e}")
        except ApiError as e:
            print(f"\n[error] API call failed: {e}")
