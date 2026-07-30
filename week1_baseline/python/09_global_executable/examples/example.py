#!/usr/bin/env python3
"""
Boukensha Step 8: The REPL Loop Example

This example demonstrates the interactive REPL for multi-turn conversations.
Config is loaded automatically - system prompt, model, and API key all
come from .boukensha (or BOUKENSHA_DIR) by default.
"""

import os
import sys
from pathlib import Path

# Config is loaded automatically inside boukensha.repl()
# Set BOUKENSHA_DIR before importing boukensha
if "BOUKENSHA_DIR" not in os.environ:
    os.environ["BOUKENSHA_DIR"] = str(
        (Path(__file__).parent.parent.parent.parent.parent / ".boukensha").resolve()
    )

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import boukensha

print(f"Config: {boukensha.config()}")
print()

# The base directory tools will operate relative to - step 07 folder
# makes a good playground since it already has source files to read
base_dir = Path(__file__).parent.parent.parent / "07_the_run_dsl"


def register_tools(dsl):
    """Register tools for the agent."""

    def read_file_impl(path: str) -> str:
        """Read the contents of a file from disk."""
        full_path = (base_dir / path).resolve()
        return full_path.read_text()

    dsl.tool(
        "read_file",
        description="Read the contents of a file from disk",
        parameters={
            "path": {
                "type": "string",
                "description": "File path (relative to the working directory)"
            }
        },
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
        parameters={
            "path": {
                "type": "string",
                "description": "Directory path (relative to working directory, or '.' for root)"
            }
        },
        implementation=list_directory_impl
    )


# Start the REPL
boukensha.repl(block=register_tools)
