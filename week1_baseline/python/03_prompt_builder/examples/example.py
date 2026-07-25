#!/usr/bin/env python3
"""
Example demonstrating the Boukensha multi-provider prompt builder.

This example shows how to use the PromptBuilder with different LLM backends
to serialize context into provider-specific API formats.
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path so we can import boukensha
sys.path.insert(0, str(Path(__file__).parent.parent))

from boukensha import Config, Context, Registry, Player
from boukensha.prompt_builder import PromptBuilder
from boukensha.backends import Anthropic, OpenAI, Gemini, Ollama, OllamaCloud

# Override the config directory so the example works from the repo root
if "BOUKENSHA_DIR" not in os.environ:
    os.environ["BOUKENSHA_DIR"] = str(
        Path(__file__).parent.parent.parent.parent.parent / ".boukensha"
    )

# Setup config and context
config = Config()
player_settings = config.tasks("player")
system_prompt = Player.system_prompt(
    player_settings,
    user_prompts_dir=config.user_prompts_dir,
    default_prompts_dir=Config.PROMPTS_DIR,
)

ctx = Context(task=Player, system=system_prompt)
registry = Registry(ctx)

# Register tools
def look_fn() -> str:
    """Look around the current room."""
    return "A damp stone corridor stretches north. Torches flicker on the walls."


def move_fn(direction: str) -> str:
    """Move the player in a direction."""
    return f"You move {direction} into a torch-lit corridor."


registry.tool(
    name="look",
    description="Look around the current room for details",
    parameters={},
    block=look_fn,
)

registry.tool(
    name="move",
    description="Move the player in a direction (north, south, east, west, up, down)",
    parameters={"direction": {"type": "string", "description": "The direction to move"}},
    block=move_fn,
)

# Add some conversation history
ctx.add_message("user", "I just arrived in the dungeon. What's around me, and can you move north?")
ctx.add_message("assistant", "Let me take a look around first.")
ctx.add_message(
    "tool_result",
    "A damp stone corridor stretches north. Torches flicker on the walls.",
    tool_use_id="toolu_01X"
)

print("=== BOUKENSHA Step 3: Prompt Builder ===")

# Get provider and model from config
provider = Player.provider(player_settings)
model = Player.model(player_settings)

# Create the appropriate backend based on provider
if provider == "anthropic":
    api_key = os.environ.get("ANTHROPIC_API_KEY", "sk-ant-test-key")
    backend = Anthropic(api_key=api_key, model=model)
elif provider == "ollama":
    backend = Ollama(model=model)
elif provider == "ollama_cloud":
    api_key = os.environ.get("OLLAMA_API_KEY", "ollama-test-key")
    backend = OllamaCloud(api_key=api_key, model=model)
elif provider == "openai":
    api_key = os.environ.get("OPENAI_API_KEY", "sk-test-key")
    backend = OpenAI(api_key=api_key, model=model)
elif provider == "gemini":
    api_key = os.environ.get("GEMINI_API_KEY", "gemini-test-key")
    backend = Gemini(api_key=api_key, model=model)
else:
    raise ValueError(f"Unsupported provider for player task: {provider}")

# Create the prompt builder
builder = PromptBuilder(context=ctx, backend=backend)

print()
print(f"Config: {config}")
print(f"Provider: {provider}")
print(f"Model: {model}")
print()
print("API Payload:")
print(json.dumps(builder.to_api_payload(), indent=2))
