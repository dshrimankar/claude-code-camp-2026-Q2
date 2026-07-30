"""
Boukensha: AI-driven MUD player agent framework.

This module provides the structural components, tool dispatch pattern,
multi-provider LLM integration, HTTP API client, and session logging
for building agent-based systems that interact with MUD servers.
"""

from boukensha.config import Config
from boukensha.context import Context
from boukensha.errors import UnknownToolError, UnsupportedModelError, ApiError, LoopError
from boukensha.message import Message
from boukensha.registry import Registry
from boukensha.tool import Tool
from boukensha.tasks.player import Player
from boukensha.prompt_builder import PromptBuilder
from boukensha.client import Client
from boukensha.agent import Agent
from boukensha.logger import Logger
from boukensha.run_dsl import RunDSL
from boukensha.repl import Repl
from boukensha import backends

# Module-level state
_quiet = False
_debug = False
_config = None


def config() -> Config:
    """Get or create the global Config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def quiet() -> None:
    """Enable quiet mode (suppress output)."""
    global _quiet
    _quiet = True


def loud() -> None:
    """Disable quiet mode (enable output)."""
    global _quiet
    _quiet = False


def is_quiet() -> bool:
    """Check if quiet mode is enabled."""
    return _quiet


def debug() -> None:
    """Enable debug mode (verbose logging)."""
    global _debug
    _debug = True


def is_debug() -> bool:
    """Check if debug mode is enabled."""
    return _debug


def run(
    *,
    task: str,
    system: str = None,
    model: str = None,
    backend: str = None,
    api_key: str = None,
    ollama_host: str = "http://localhost:11434",
    log: str = None,
    max_output_tokens: int = None,
    block: callable = None
) -> str:
    """Top-level DSL entry point for Boukensha.

    Wires together all components so the caller only describes *what* to do.

    Args:
        task: The user message to give the agent (required)
        system: System prompt (defaults to task's system prompt)
        model: Model name (defaults to task's model setting)
        backend: "anthropic", "openai", "gemini", "ollama", or "ollama_cloud"
        api_key: API key for the backend (defaults to env var)
        ollama_host: Ollama base URL (default: http://localhost:11434)
        log: Optional JSONL log path (defaults to .boukensha/sessions/<id>.jsonl)
        max_output_tokens: Max tokens per response (defaults to task setting)
        block: Optional callable for tool registration: block(dsl: RunDSL) -> None

    Returns:
        The agent's final text response

    Example:
        def my_tools(dsl):
            dsl.tool("read_file",
                     description="Read a file",
                     parameters={"path": {"type": "string"}},
                     implementation=lambda path: open(path).read())

        result = boukensha.run(task="Read README.md", block=my_tools)
    """
    import os

    # Load config (triggers .env loading)
    cfg = config()
    task_class = Player
    task_settings = cfg.tasks(task_class.task_name())

    # Set defaults from task settings
    if system is None:
        system = task_class.system_prompt(
            task_settings,
            user_prompts_dir=cfg.user_prompts_dir,
            default_prompts_dir=Config.PROMPTS_DIR
        )
    if model is None:
        model = task_class.model(task_settings)
    if backend is None:
        backend = task_class.provider(task_settings)

    # Set default API key based on backend
    if api_key is None:
        api_key_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "ollama_cloud": "OLLAMA_API_KEY",
        }
        env_var = api_key_map.get(backend)
        if env_var:
            api_key = os.getenv(env_var)

    # Create context and registry
    ctx = Context(task=task_class, system=system)
    registry = Registry(ctx)

    # Execute block with RunDSL if provided
    if block:
        dsl = RunDSL(registry)
        block(dsl)

    # Create backend instance
    backend_factories = {
        "anthropic": lambda: backends.Anthropic(api_key=api_key, model=model),
        "openai": lambda: backends.OpenAI(api_key=api_key, model=model),
        "gemini": lambda: backends.Gemini(api_key=api_key, model=model),
        "ollama": lambda: backends.Ollama(host=ollama_host, model=model),
        "ollama_cloud": lambda: backends.OllamaCloud(api_key=api_key, model=model),
    }

    if backend not in backend_factories:
        raise ValueError(
            f"Unknown backend {backend!r}. "
            f"Use 'anthropic', 'openai', 'gemini', 'ollama', or 'ollama_cloud'."
        )

    be = backend_factories[backend]()

    # Create the rest of the components
    builder = PromptBuilder(ctx, be)
    client = Client(builder)
    effective_max_iterations = task_class.max_iterations(task_settings)
    effective_max_output_tokens = (
        max_output_tokens
        if max_output_tokens is not None
        else task_class.max_output_tokens(task_settings)
    )
    logger = Logger(
        log=log,
        snapshot={
            "task": task_class.task_name(),
            "max_iterations": effective_max_iterations,
            "max_output_tokens": effective_max_output_tokens,
            "model": model,
            "provider": backend,
        },
    )
    agent = Agent(
        context=ctx,
        registry=registry,
        builder=builder,
        client=client,
        logger=logger,
        task_settings=task_settings,
        max_iterations=effective_max_iterations,
        max_output_tokens=effective_max_output_tokens,
    )

    # Run the agent
    try:
        ctx.add_message("user", task)
        return agent.run()
    finally:
        if logger:
            logger.close()


def repl(
    *,
    system: str = None,
    model: str = None,
    backend: str = None,
    api_key: str = None,
    ollama_host: str = "http://localhost:11434",
    log: str = None,
    max_output_tokens: int = None,
    block: callable = None
) -> None:
    """Interactive REPL for multi-turn conversations.

    Same setup as run() but enters an interactive loop instead of
    processing a single task. The REPL maintains conversation history
    across turns.

    Args:
        system: System prompt (defaults to task's system prompt)
        model: Model name (defaults to task's model setting)
        backend: "anthropic", "openai", "gemini", "ollama", or "ollama_cloud"
        api_key: API key for the backend (defaults to env var)
        ollama_host: Ollama base URL (default: http://localhost:11434)
        log: Optional JSONL log path
        max_output_tokens: Max tokens per response (defaults to task setting)
        block: Optional callable for tool registration: block(dsl: RunDSL) -> None

    Example:
        def my_tools(dsl):
            dsl.tool("read_file",
                     description="Read a file",
                     parameters={"path": {"type": "string"}},
                     implementation=lambda path: open(path).read())

        boukensha.repl(block=my_tools)  # Starts interactive REPL
    """
    import os

    # Load config (triggers .env loading)
    cfg = config()
    task_class = Player
    task_settings = cfg.tasks(task_class.task_name())

    # Set defaults from task settings
    if system is None:
        system = task_class.system_prompt(
            task_settings,
            user_prompts_dir=cfg.user_prompts_dir,
            default_prompts_dir=Config.PROMPTS_DIR
        )
    if model is None:
        model = task_class.model(task_settings)
    if backend is None:
        backend = task_class.provider(task_settings)

    # Set default API key based on backend
    if api_key is None:
        api_key_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "ollama_cloud": "OLLAMA_API_KEY",
        }
        env_var = api_key_map.get(backend)
        if env_var:
            api_key = os.getenv(env_var)

    # Create context and registry
    ctx = Context(task=task_class, system=system)
    registry = Registry(ctx)

    # Execute block with RunDSL if provided
    if block:
        dsl = RunDSL(registry)
        block(dsl)

    # Create backend instance
    backend_factories = {
        "anthropic": lambda: backends.Anthropic(api_key=api_key, model=model),
        "openai": lambda: backends.OpenAI(api_key=api_key, model=model),
        "gemini": lambda: backends.Gemini(api_key=api_key, model=model),
        "ollama": lambda: backends.Ollama(host=ollama_host, model=model),
        "ollama_cloud": lambda: backends.OllamaCloud(api_key=api_key, model=model),
    }

    if backend not in backend_factories:
        raise ValueError(
            f"Unknown backend {backend!r}. "
            f"Use 'anthropic', 'openai', 'gemini', 'ollama', or 'ollama_cloud'."
        )

    be = backend_factories[backend]()

    # Create the rest of the components
    builder = PromptBuilder(ctx, be)
    client = Client(builder)
    effective_max_iterations = task_class.max_iterations(task_settings)
    effective_max_output_tokens = (
        max_output_tokens
        if max_output_tokens is not None
        else task_class.max_output_tokens(task_settings)
    )
    logger = Logger(
        log=log,
        snapshot={
            "task": task_class.task_name(),
            "max_iterations": effective_max_iterations,
            "max_output_tokens": effective_max_output_tokens,
            "model": model,
            "provider": backend,
        },
    )

    # Start the REPL
    try:
        Repl(
            context=ctx,
            registry=registry,
            builder=builder,
            client=client,
            logger=logger,
            task_settings=task_settings,
            max_iterations=effective_max_iterations,
            max_output_tokens=effective_max_output_tokens,
            config_dir=cfg.dir,
            provider=backend,
            model=model,
            version=__version__,
            api_key=api_key,
        ).start()
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        if logger:
            logger.close()


__all__ = [
    "Config",
    "Context",
    "Message",
    "Registry",
    "Tool",
    "RunDSL",
    "Repl",
    "UnknownToolError",
    "UnsupportedModelError",
    "ApiError",
    "LoopError",
    "Player",
    "PromptBuilder",
    "Client",
    "Agent",
    "Logger",
    "backends",
    "config",
    "quiet",
    "loud",
    "is_quiet",
    "debug",
    "is_debug",
    "run",
    "repl",
]

__version__ = "0.9.0"
