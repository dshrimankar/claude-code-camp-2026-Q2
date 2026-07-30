"""
MCP (Model Context Protocol) client for stdio transport.

Client is a minimal MCP-over-stdio client: it spawns an MCP server as a
subprocess, performs the initialize handshake, and lets you discover and
call the tools it advertises. It knows nothing about any particular
server — command, args, and env are the standard stdio transport config.

Example:
    client = McpClient.spawn(command="mud-manager", args=["--mcp"])
    for tool in client.tools:
        print(tool["name"])
    result = client.call_tool("look")
    print(result["text"])
    client.close()
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional


class McpClient:
    """MCP-over-stdio client for spawning and communicating with MCP servers."""

    class Error(Exception):
        """MCP client error."""
        pass

    PROTOCOL_VERSION = "2025-06-18"

    def __init__(self, process: subprocess.Popen, stdin: io.TextIOWrapper, stdout: io.TextIOWrapper):
        """Initialize MCP client with subprocess and I/O streams.

        Args:
            process: The subprocess running the MCP server
            stdin: Text wrapper for stdin
            stdout: Text wrapper for stdout
        """
        self._process = process
        self._stdin = stdin
        self._stdout = stdout
        self._id = 0

        # Perform handshake and discover tools
        self._handshake()
        self.tools = self._fetch_tools()

    @classmethod
    def spawn(cls, command: str, args: Optional[List[str]] = None, env: Optional[Dict[str, str]] = None) -> McpClient:
        """Spawn an MCP server as a subprocess and create a client.

        Args:
            command: Executable to spawn
            args: Arguments for the command
            env: Extra environment variables (merged with current env)

        Returns:
            McpClient instance

        Raises:
            Error: If subprocess fails to start
        """
        if args is None:
            args = []
        if env is None:
            env = {}

        # Build command list
        cmd = [str(command)] + [str(arg) for arg in args]

        # Merge environment
        import os
        merged_env = {**os.environ, **{str(k): str(v) for k, v in env.items()}}

        try:
            # Spawn subprocess with pipes (binary mode)
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=merged_env,
                text=False  # Binary mode for proper buffering
            )

            # Wrap with TextIOWrapper for line-buffered text I/O
            stdin_wrapper = io.TextIOWrapper(
                process.stdin,
                encoding='utf-8',
                line_buffering=True,
                write_through=True
            )
            stdout_wrapper = io.TextIOWrapper(
                process.stdout,
                encoding='utf-8',
                line_buffering=True
            )

            return cls(process, stdin_wrapper, stdout_wrapper)

        except (OSError, FileNotFoundError) as e:
            raise cls.Error(f"Failed to spawn MCP server '{command}': {e}")

    @property
    def server_info(self) -> Optional[Dict[str, Any]]:
        """Server information from handshake."""
        return self._server_info

    def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call a tool on the MCP server.

        Args:
            name: Tool name
            arguments: Tool arguments (default: {})

        Returns:
            Dict with keys:
                - text: Text content from response
                - error: Boolean indicating if tool returned an error

        Raises:
            Error: If the request fails
        """
        if arguments is None:
            arguments = {}

        response = self._request("tools/call", {
            "name": str(name),
            "arguments": arguments
        })

        result = response.get("result")
        if result is None:
            error_info = response.get("error", {})
            raise self.Error(f"tools/call error: {error_info}")

        # Extract text from content blocks
        content = result.get("content", [])
        if not isinstance(content, list):
            content = []

        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))

        return {
            "text": "\n".join(text_parts),
            "error": bool(result.get("isError", False))
        }

    def close(self) -> None:
        """Close the MCP client and cleanup subprocess."""
        try:
            self._stdin.close()
        except Exception:
            pass

        try:
            # Wait for process to exit
            self._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't exit cleanly
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()

        try:
            self._stdout.close()
        except Exception:
            pass

    def _handshake(self) -> None:
        """Perform MCP protocol handshake."""
        # Import here to avoid circular dependency
        try:
            from boukensha import __version__
        except ImportError:
            __version__ = "unknown"

        response = self._request("initialize", {
            "protocolVersion": self.PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {
                "name": "boukensha",
                "version": __version__
            }
        })

        self._server_info = response.get("result", {}).get("serverInfo")

        # Send initialized notification
        self._notify("notifications/initialized")

    def _fetch_tools(self) -> List[Dict[str, Any]]:
        """Fetch list of tools from the server.

        Returns:
            List of tool descriptions
        """
        response = self._request("tools/list")
        result = response.get("result", {})
        return result.get("tools", [])

    def _request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request and wait for response.

        Args:
            method: JSON-RPC method name
            params: Request parameters

        Returns:
            Response object

        Raises:
            Error: If connection is closed or JSON parsing fails
        """
        if params is None:
            params = {}

        self._id += 1
        request_id = self._id

        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }

        self._write(payload)
        return self._read_until(request_id)

    def _notify(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Send a JSON-RPC notification (no response expected).

        Args:
            method: JSON-RPC method name
            params: Notification parameters
        """
        if params is None:
            params = {}

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }

        self._write(payload)

    def _write(self, obj: Dict[str, Any]) -> None:
        """Write a JSON object as a line to stdin.

        Args:
            obj: Object to serialize and write
        """
        line = json.dumps(obj) + '\n'
        self._stdin.write(line)
        self._stdin.flush()

    def _read_until(self, request_id: int) -> Dict[str, Any]:
        """Read JSON lines from stdout until we find the matching response.

        Args:
            request_id: The request ID to match

        Returns:
            The matching response object

        Raises:
            Error: If connection is closed or JSON parsing fails
        """
        while True:
            line = self._stdout.readline()

            if not line:
                raise self.Error("server closed the connection")

            line = line.strip()
            if not line:
                continue

            try:
                msg = json.loads(line)
            except json.JSONDecodeError as e:
                raise self.Error(f"Invalid JSON from server: {e}")

            # Return if this is the response we're waiting for
            if msg.get("id") == request_id:
                return msg

            # Ignore server-initiated notifications or mismatched IDs
