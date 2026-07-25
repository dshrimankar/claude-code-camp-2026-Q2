#!/usr/bin/env python3
"""
Example demonstrating the Boukensha tool registry pattern.

This example shows how to use the Registry to register and dispatch tools.
The agent never calls tools directly - it emits structured requests that
the Registry dispatches.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path so we can import boukensha
sys.path.insert(0, str(Path(__file__).parent.parent))

from boukensha import Config, Context, Registry, Player, UnknownToolError

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
registry = Registry(ctx)

# Notice that we now register the tools through the registry instead of directly
# on the context in the previous step.
# They will still be attached to context which is why we pass it into
# our registry when we initialize it.


def move_fn(direction: str) -> str:
    """Move the player in a direction."""
    return f"You move {direction} into a torch-lit corridor."


def shout_fn(message: str) -> str:
    """Shout a message to the zone."""
    return message.upper()


registry.tool(
    name="move",
    description="Move the player in a direction (north, south, east, west, up, down)",
    parameters={"direction": {"type": "string"}},
    block=move_fn,
)

registry.tool(
    name="shout",
    description="Shout a message so everyone in the zone can hear it",
    parameters={"message": {"type": "string"}},
    block=shout_fn,
)

print("=== BOUKENSHA Step 2: Tool Registry ===")
print()
print(f"Config:  {config}")
print(f"System:  {ctx.system}")
print(f"Context: {ctx}")
print("Tools:")
for tool in ctx.tools.values():
    print(f"  {tool}")
print()

# Here we are mimicking what the agent would do when
# it needs to call a tool from the registry. We are
# still missing the actual code that would decide when
# to call the registry for a tool.
print("Dispatching 'shout' with message='dragon spotted'...")
result = registry.dispatch("shout", {"message": "dragon spotted"})
print(f"Result: {result}")
print()

print("Dispatching 'move' with direction='north'...")
result = registry.dispatch("move", {"direction": "north"})
print(f"Result: {result}")
print()

try:
    registry.dispatch("flee")
except UnknownToolError as e:
    print(f"UnknownToolError caught: {e}")
