"""
MCP tools integration - makes Boukensha an MCP host.

Point it at any MCP server and every tool that server advertises becomes a
boukensha tool. It knows nothing about any particular server — command/args/env
is the standard stdio transport config, the same triple every other MCP host uses.

Example:
    from boukensha.tools import mcp

    mcp.register(
        registry,
        command="mud-manager",
        args=["--mcp"],
        env={"MUD_HOST": "localhost"},
        prefix="tbamud"
    )

The registry can be anything with a #tool method — a Registry or the RunDSL
yielded to a run/repl block.

Prefix: scopes the discovered names ("tbamud" => tbamud__look). The prefix is
a property of the server entry, supplied by config; this module applies whatever
it is given. Names are only prefixed agent-side — the server still sees its own
bare name on the wire.
"""

from __future__ import annotations

import atexit
from typing import Any, Callable, Dict, List, Optional

from boukensha.mcp.client import McpClient
from boukensha.errors import CollisionError


SEPARATOR = "__"


def register(
    registry: Any,
    command: str,
    args: Optional[List[str]] = None,
    env: Optional[Dict[str, str]] = None,
    prefix: Optional[str] = None
) -> int:
    """Spawn an MCP server and register all its tools.

    Args:
        registry: Object with #tool method (Registry or RunDSL)
        command: Executable to spawn
        args: Arguments for the command
        env: Extra environment variables
        prefix: Name prefix to avoid collisions (e.g., "tbamud")

    Returns:
        Number of tools registered

    Raises:
        CollisionError: If tool names collide
        McpClient.Error: If server fails to spawn
    """
    if args is None:
        args = []
    if env is None:
        env = {}

    client = McpClient.spawn(command=command, args=args, env=env)

    # Close the server subprocess cleanly when the agent process exits
    def cleanup():
        try:
            client.close()
        except Exception:
            pass

    atexit.register(cleanup)

    return register_client(registry, client, prefix=prefix)


def register_client(
    registry: Any,
    client: McpClient,
    prefix: Optional[str] = None
) -> int:
    """Register an already-spawned client's tools.

    Args:
        registry: Object with #tool method (Registry or RunDSL)
        client: MCP client with tools already discovered
        prefix: Name prefix to avoid collisions

    Returns:
        Number of tools registered

    Raises:
        CollisionError: If tool names collide
    """
    # Get already-registered tool names to detect collisions
    taken = []
    if hasattr(registry, 'tool_names') and callable(registry.tool_names):
        taken = list(registry.tool_names())

    for tool in client.tools:
        remote = tool["name"]
        local = prefixed(remote, prefix)

        if local in taken:
            raise CollisionError(
                f"boukensha: MCP tool name collision on '{local}' — a tool by that "
                f"name is already registered. Give this server a distinct `prefix:` "
                f"in mcp_servers."
            )
        taken.append(local)

        # Convert MCP tool schema to Boukensha parameters
        description = str(tool.get("description", ""))
        parameters = to_boukensha_params(tool.get("inputSchema"))

        # Create tool implementation that calls MCP server
        def make_tool_impl(client_ref: McpClient, remote_name: str) -> Callable:
            """Create tool implementation closure.

            Args:
                client_ref: MCP client reference
                remote_name: Tool name on the server (unprefixed)

            Returns:
                Callable that executes the tool
            """
            def tool_impl(**kwargs):
                # Boukensha hands us symbol-keyed kwargs; the server wants strings
                # Blank/omitted values are normalized server-side
                str_kwargs = {str(k): v for k, v in kwargs.items()}
                result = client_ref.call_tool(remote_name, str_kwargs)

                if result.get("error"):
                    return f"error: {result['text']}"
                return result["text"]

            return tool_impl

        # Register the tool with the registry
        registry.tool(
            local,
            description=description,
            parameters=parameters,
            block=make_tool_impl(client, remote)
        )

    return len(client.tools)


def prefixed(name: str, prefix: Optional[str]) -> str:
    """Apply prefix to tool name with separator.

    Args:
        name: Base tool name
        prefix: Optional prefix

    Returns:
        Prefixed name (e.g., "tbamud__look") or bare name if no prefix
    """
    if prefix is None:
        return str(name)

    p = str(prefix).strip()
    if not p:
        return str(name)

    return f"{p}{SEPARATOR}{name}"


def to_boukensha_params(input_schema: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert an MCP inputSchema into boukensha's parameters shape.

    We list every property so the model can supply optional ones too
    (servers treat blanks as absent).

    Args:
        input_schema: MCP inputSchema object

    Returns:
        Dict mapping parameter names to {type, description}

    Example:
        MCP format:
        {
            "properties": {
                "direction": {
                    "type": "string",
                    "description": "Which way to move",
                    "enum": ["north", "south", "east", "west"]
                }
            }
        }

        Boukensha format:
        {
            "direction": {
                "type": "string",
                "description": "Which way to move (one of: north, south, east, west)"
            }
        }
    """
    if not input_schema:
        return {}

    properties = input_schema.get("properties", {})
    result = {}

    for pname, schema in properties.items():
        desc = str(schema.get("description", ""))

        # Add enum values to description if present
        if "enum" in schema and schema["enum"]:
            enum_list = ", ".join(str(v) for v in schema["enum"])
            desc = f"{desc} (one of: {enum_list})".strip()

        result[pname] = {
            "type": schema.get("type", "string"),
            "description": desc
        }

    return result
