#!/usr/bin/env python3
"""
Boukensha Step 6: The Logger Example

This example demonstrates the complete agent loop with structured JSONL logging.
The logger records all agent activities (iterations, prompts, tool calls, responses)
to session-based JSONL files in .boukensha/sessions/
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from boukensha import (
    Config,
    Context,
    Registry,
    Player,
    PromptBuilder,
    Client,
    Agent,
    Logger,
    backends
)


def main():
    # Set BOUKENSHA_DIR to point to the .boukensha folder in the repo root
    if "BOUKENSHA_DIR" not in os.environ:
        os.environ["BOUKENSHA_DIR"] = str(
            (Path(__file__).parent.parent.parent.parent.parent / ".boukensha").resolve()
        )

    # Setup configuration
    config = Config()
    player_settings = config.tasks("player")
    system_prompt = Player.system_prompt(
        player_settings,
        user_prompts_dir=config.user_prompts_dir,
        default_prompts_dir=Config.PROMPTS_DIR
    )
    base_dir = Path(__file__).parent.parent

    # Create context and registry
    ctx = Context(task=Player, system=system_prompt)
    registry = Registry(ctx)

    # Get provider and model from settings
    provider = Player.provider(player_settings)
    model = Player.model(player_settings)

    # Create backend based on provider
    if provider == "anthropic":
        backend = backends.Anthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            model=model
        )
    elif provider == "openai":
        backend = backends.OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            model=model
        )
    elif provider == "gemini":
        backend = backends.Gemini(
            api_key=os.environ["GEMINI_API_KEY"],
            model=model
        )
    elif provider == "ollama":
        backend = backends.Ollama(model=model)
    elif provider == "ollama_cloud":
        backend = backends.OllamaCloud(
            api_key=os.environ["OLLAMA_API_KEY"],
            model=model
        )
    else:
        raise ValueError(f"Unsupported provider for player task: {provider}")

    # Create logger with session metadata
    logger = Logger(
        snapshot={
            "provider": provider,
            "model": model,
            "task": "player",
            "example": "06_the_logger"
        }
    )

    # Create builder, client, and agent
    builder = PromptBuilder(context=ctx, backend=backend)
    client = Client(builder)
    agent = Agent(
        context=ctx,
        registry=registry,
        builder=builder,
        client=client,
        logger=logger,
        task_settings=player_settings
    )

    # Register tools
    def read_file(path: str) -> str:
        """Read the contents of a file from disk."""
        file_path = (base_dir / path).resolve()
        with open(file_path, 'r') as f:
            return f.read()

    def list_directory(path: str) -> str:
        """List the files in a directory."""
        dir_path = (base_dir / path).resolve()
        entries = [f.name for f in dir_path.iterdir() if not f.name.startswith('.')]
        return ", ".join(sorted(entries))

    registry.tool(
        name="read_file",
        description="Read the contents of a file from disk",
        parameters={
            "path": {"type": "string", "description": "The file path to read"}
        },
        block=read_file
    )

    registry.tool(
        name="list_directory",
        description="List the files in a directory",
        parameters={
            "path": {"type": "string", "description": "The directory path to list"}
        },
        block=list_directory
    )

    # Add user message
    ctx.add_message("user", "Read the README.md file and summarise what this MUD player assistant framework can do.")

    # Display configuration
    print("=== BOUKENSHA Step 6: The Logger ===")
    print()
    print(f"Config: {config}")
    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print(f"Max iterations: {Player.max_iterations(player_settings)}")
    print(f"Max output tokens: {Player.max_output_tokens(player_settings)}")
    print(f"Session log: {logger.log_file}")
    print()

    # Run the agent
    result = agent.run()

    # Display final response
    print()
    print("=== FINAL RESPONSE ===")
    print(result)
    print()
    print(f"Session log saved to: {logger.log_file}")

    # Close logger
    logger.close()


if __name__ == "__main__":
    main()
