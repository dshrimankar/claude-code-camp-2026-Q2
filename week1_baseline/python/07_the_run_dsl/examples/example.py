#!/usr/bin/env python3
"""
Boukensha Step 7: The Boukensha.run DSL Example

This example demonstrates the top-level DSL that hides all plumbing.
Config is loaded automatically - system prompt, model, and API key all
come from .boukensha (or BOUKENSHA_DIR) by default.
"""

import os
import sys
from pathlib import Path

# Set BOUKENSHA_DIR to point to .boukensha in repo root
if "BOUKENSHA_DIR" not in os.environ:
    os.environ["BOUKENSHA_DIR"] = str(
        (Path(__file__).parent.parent.parent.parent.parent / ".boukensha").resolve()
    )

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import boukensha

# Config is loaded automatically inside boukensha.run() — system prompt, model,
# and API key all come from .boukensha (or BOUKENSHA_DIR) by default.
# You can override any of them as keyword arguments if you want.

print("=== BOUKENSHA Step 7: The Boukensha.run DSL ===")
print()
print(f"Config: {boukensha.config()}")
print()

base_dir = Path(__file__).parent.parent


def register_tools(dsl):
    """Register tools for the agent."""

    def read_file_impl(path: str) -> str:
        """Read the contents of a file from disk."""
        full_path = (base_dir / path).resolve()
        return full_path.read_text()

    dsl.tool(
        "read_file",
        description="Read the contents of a file from disk",
        parameters={"path": {"type": "string", "description": "The file path to read"}},
        implementation=read_file_impl
    )

    def list_directory_impl(path: str) -> str:
        """List the files in a directory."""
        full_path = (base_dir / path).resolve()
        entries = [
            e.name for e in full_path.iterdir()
            if not e.name.startswith(".")
        ]
        return ", ".join(sorted(entries))

    dsl.tool(
        "list_directory",
        description="List the files in a directory",
        parameters={"path": {"type": "string", "description": "The directory path to list"}},
        implementation=list_directory_impl
    )


result = boukensha.run(
    task="Read the README.md file and summarise what this MUD player assistant framework can do.",
    block=register_tools
)

print()
print("=== FINAL RESPONSE ===")
print(result)
