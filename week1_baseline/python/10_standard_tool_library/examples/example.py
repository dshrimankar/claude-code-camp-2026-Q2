#!/usr/bin/env python3
"""
Boukensha Step 10: Standard Tool Library (MCP Host) Example

This example demonstrates Boukensha as a pure MCP host. All tools come from
external MCP servers configured in settings.yaml. No manual tool registration
needed!

Configure your MCP servers in .boukensha/settings.yaml:

  mcp_servers:
    filesystem:
      command: npx
      args: [-y, "@modelcontextprotocol/server-filesystem", /tmp]
      prefix: fs
    mud:
      command: mud-manager
      args: [--mcp]
      prefix: tbamud
      env:
        MUD_HOST: your.mud.host
        MUD_PORT: 4000

Each server's tools are automatically discovered and registered when the
agent starts. The `prefix:` prevents name collisions between servers.
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

# Start the REPL
# Tools come from mcp_servers in config automatically - no manual registration!
boukensha.repl()
