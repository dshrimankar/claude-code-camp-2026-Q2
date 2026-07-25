#!/usr/bin/env python3
"""
Example demonstrating the Boukensha struct skeleton.

This example shows how to create and use the core data structures:
Tool, Message, and Context.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict

# Add parent directory to path so we can import boukensha
sys.path.insert(0, str(Path(__file__).parent.parent))

from boukensha import Config, Context, Tool, Player

# Override the config directory so the example works from the repo root.
# In real usage a user's ~/.boukensha is picked up automatically.
if "BOUKENSHA_DIR" not in os.environ:
    os.environ["BOUKENSHA_DIR"] = str(
        Path(__file__).parent.parent.parent.parent.parent / ".boukensha"
    )

config = Config()
player_settings = config.tasks("player")
system_prompt = Player.system_prompt(
    player_settings,
    user_prompts_dir=config.user_prompts_dir,
    default_prompts_dir=Config.PROMPTS_DIR,
)

ctx = Context(task=Player, system=system_prompt)

# Define a simple move function
def move_fn(args: Dict[str, Any]) -> str:
    """Execute a move command."""
    direction = args.get("direction", "unknown")
    return f"You move {direction} into a torch-lit corridor."

ctx.register_tool(
    Tool(
        name="move",
        description="Move the player in a direction (north, south, east, west, up, down)",
        parameters={
            "direction": {"type": "string", "description": "The direction to move"}
        },
        block=move_fn,
    )
)

ctx.add_message("user", "Explore north and tell me what you find.")
ctx.add_message("assistant", "Sure, let me head north and take a look.")

print("=== Boukensha Step 1: Struct Skeleton ===")
print()
print(f"Config:   {config}")
print(f"System:   {ctx.system}")
print(f"Context:  {ctx}")
print(f"Tool:     {ctx.tools['move']}")
print("Messages:")
for m in ctx.messages:
    print(f"  {m}")
