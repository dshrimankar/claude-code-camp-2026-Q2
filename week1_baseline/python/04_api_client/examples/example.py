#!/usr/bin/env python3
"""
Example demonstrating the Boukensha API client.

This example shows how to make real API calls to LLM providers using
the Client class with retry logic and error handling.
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path so we can import boukensha
sys.path.insert(0, str(Path(__file__).parent.parent))

from boukensha import Config, Context, Registry, Player
from boukensha.prompt_builder import PromptBuilder
from boukensha.client import Client
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
def read_file(path: str) -> str:
    """Read the contents of a file from disk."""
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


def list_directory(path: str) -> str:
    """List files in a directory."""
    try:
        entries = []
        for entry in Path(path).iterdir():
            if not entry.name.startswith('.'):
                entries.append(entry.name)
        return '\n'.join(sorted(entries)) if entries else "(empty directory)"
    except Exception as e:
        return f"Error listing directory: {e}"


registry.tool(
    name="read_file",
    description="Read the contents of a file from disk",
    parameters={"path": {"type": "string", "description": "The file path to read"}},
    block=read_file,
)

registry.tool(
    name="list_directory",
    description="List files in a directory",
    parameters={"path": {"type": "string", "description": "The directory path to list"}},
    block=list_directory,
)

# Add user message
ctx.add_message("user", "What files are in the current directory?")

print("=== BOUKENSHA Step 4: API Client ===")
print()

# Get provider and model from config
provider = Player.provider(player_settings)
model = Player.model(player_settings)

# Create the appropriate backend based on provider
if provider == "anthropic":
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)
    backend = Anthropic(api_key=api_key, model=model)
elif provider == "openai":
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    backend = OpenAI(api_key=api_key, model=model)
elif provider == "gemini":
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        sys.exit(1)
    backend = Gemini(api_key=api_key, model=model)
elif provider == "ollama":
    backend = Ollama(model=model)
elif provider == "ollama_cloud":
    api_key = os.environ.get("OLLAMA_API_KEY", "")
    if not api_key:
        print("Error: OLLAMA_API_KEY environment variable not set")
        sys.exit(1)
    backend = OllamaCloud(api_key=api_key, model=model)
else:
    print(f"Error: Unsupported provider for player task: {provider}")
    sys.exit(1)

# Create prompt builder and client
builder = PromptBuilder(context=ctx, backend=backend)
client = Client(builder)

print(f"Config: {config}")
print(f"Provider: {provider}")
print(f"Model: {model}")
print(f"Sending request to {builder.url}...")
print()

# Make API call
try:
    response = client.call()
    print("Raw response:")
    print(json.dumps(response, indent=2))
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
