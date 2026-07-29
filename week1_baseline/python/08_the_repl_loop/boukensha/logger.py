"""
Structured JSON Lines logger for agent sessions.

Logs all agent activities (iterations, prompts, tool calls, responses) to
session-based JSONL files in .boukensha/sessions/
"""

from __future__ import annotations
import json
import secrets
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from boukensha.message import Message
    from boukensha.tool import Tool
    from boukensha.backends.base import Base


class Logger:
    """
    Session-based JSONL logger for agent activities.

    Creates a unique session file at .boukensha/sessions/<session-id>.jsonl
    and logs all agent events as JSON Lines.

    Example:
        >>> logger = Logger()
        >>> logger.iteration(n=1, max=25)
        >>> logger.prompt(messages=[...], tools={...})
        >>> logger.response(text="...", usage={...}, ...)
    """

    DEFAULT_SESSION_DIR = "sessions"

    def __init__(
        self,
        session_id: Optional[str] = None,
        dir: Optional[str] = None,
        log: Optional[str] = None,
        snapshot: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize logger with optional session ID and directory.

        Args:
            session_id: Optional session ID (generated if not provided)
            dir: Optional sessions directory (uses config default if not provided)
            log: Optional explicit log file path (overrides session_id/dir)
            snapshot: Optional metadata to include in session_start event
        """
        self.session_id = session_id or self._generate_session_id()

        if log:
            self.log_file = log
        else:
            log_dir = dir or self._default_dir()
            self.log_file = str(Path(log_dir) / f"{self.session_id}.jsonl")

        # Ensure directory exists
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)

        # Open file in append mode
        self._log_io = open(self.log_file, 'a')

        # Write session start event
        session_start = {"phase": "session_start"}
        if snapshot:
            session_start.update(snapshot)
        self._write_log(session_start)

    def turn(self, n: int) -> None:
        """Log REPL turn header."""
        import boukensha
        self._write_log({"phase": "turn", "n": n})
        if not boukensha.is_quiet():
            print(f"\n╔══ turn {n} ══╗")

    def iteration(self, n: int, max: int) -> None:
        """Log iteration counter."""
        self._write_log({"phase": "iteration", "n": n, "max": max})

    def limit_reached(self, kind: str, n: int, max: int) -> None:
        """Log when a limit is reached (e.g., max_iterations)."""
        self._write_log({"phase": "limit_reached", "kind": kind, "n": n, "max": max})

    def turn_end(
        self, reason: str, iterations: int, tokens: Optional[Dict[str, int]] = None
    ) -> None:
        """Log turn completion with summary statistics."""
        event: Dict[str, Any] = {
            "phase": "turn_end",
            "reason": reason,
            "iterations": iterations
        }
        if tokens is not None:
            event["tokens"] = tokens
        self._write_log(event)

    def prompt(self, messages: List[Message], tools: Dict[str, Tool]) -> None:
        """Log messages and tools sent to the API."""
        self._write_log({
            "phase": "prompt",
            "message_count": len(messages),
            "messages": [self._serialize_message(m) for m in messages],
            "tool_count": len(tools),
            "tools": list(tools.keys())
        })

    def tool_call(self, name: str, args: Dict[str, Any]) -> None:
        """Log tool invocation."""
        self._write_log({"phase": "tool_call", "name": name, "args": args})

    def tool_result(
        self, name: str, result: Any, ok: bool = True, error: Optional[str] = None
    ) -> None:
        """Log tool execution result."""
        event: Dict[str, Any] = {
            "phase": "tool_result",
            "name": name,
            "result": str(result),
            "ok": ok
        }
        if error is not None:
            event["error"] = error
        self._write_log(event)

    def response(
        self,
        text: str,
        usage: Optional[Dict[str, Any]] = None,
        stop_reason: Optional[str] = None,
        task: Optional[type] = None,
        backend: Optional[Base] = None
    ) -> None:
        """Log model response with metadata."""
        event: Dict[str, Any] = {
            "phase": "response",
            "text": text.strip(),
            "usage": usage,
            "stop_reason": stop_reason
        }

        # Merge execution metadata
        metadata = self._execution_metadata(task=task, backend=backend, usage=usage)
        event.update(metadata)

        self._write_log(event)

    def raw(self, data: Dict[str, Any]) -> None:
        """Log raw API response (debug mode only)."""
        # Import here to avoid circular dependency
        import boukensha
        if not boukensha.is_debug():
            return

        self._write_log({"phase": "raw", "data": data})

    def close(self) -> None:
        """Close the log file."""
        if self._log_io:
            self._log_io.close()
            self._log_io = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close file."""
        self.close()

    # Private methods

    def _default_dir(self) -> str:
        """Get default sessions directory from config."""
        import boukensha
        return str(Path(boukensha.config().dir) / self.DEFAULT_SESSION_DIR)

    def _write_log(self, event: Dict[str, Any]) -> None:
        """Write JSON event to log file with session_id and timestamp."""
        # Add session metadata
        event_with_meta = {
            **event,
            "session_id": self.session_id,
            "at": datetime.now().isoformat()
        }

        # Write as JSON line
        self._log_io.write(json.dumps(event_with_meta) + '\n')
        self._log_io.flush()

    def _generate_session_id(self) -> str:
        """Generate unique session ID: YYYYMMDDTHHMMSSZ-{8hex}."""
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        random_hex = secrets.token_hex(4)
        return f"{timestamp}-{random_hex}"

    def _serialize_message(self, msg: Message) -> Dict[str, Any]:
        """Convert Message to loggable dict."""
        return {"role": msg.role, "content": msg.content}

    def _execution_metadata(
        self,
        task: Optional[type] = None,
        backend: Optional[Base] = None,
        usage: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extract execution metadata (tokens, cost, model info)."""
        if not (task or backend or usage):
            return {}

        tokens = self._usage_tokens(usage)

        metadata: Dict[str, Any] = {
            "task": self._task_name(task),
            "provider": self._provider_name(backend),
            "model": backend.model if backend else None,
            "usage_unit": backend.usage_unit if backend and hasattr(backend, 'usage_unit') else None,
            "usage_level": backend.usage_level if backend and hasattr(backend, 'usage_level') else None,
            "input_tokens": tokens.get("input") if tokens else None,
            "output_tokens": tokens.get("output") if tokens else None,
            "cost_usd": self._estimate_cost(backend, tokens)
        }

        # Remove None values (Python equivalent of Ruby's compact)
        return {k: v for k, v in metadata.items() if v is not None}

    def _task_name(self, task: Optional[type]) -> Optional[str]:
        """Get task name from task class."""
        if task is None:
            return None
        if hasattr(task, 'task_name'):
            return task.task_name()
        return str(task)

    def _provider_name(self, backend: Optional[Base]) -> Optional[str]:
        """Get provider name from backend class name."""
        if backend is None:
            return None

        # Get class name (e.g., "Anthropic" from "boukensha.backends.anthropic.Anthropic")
        class_name = backend.__class__.__name__

        # Convert CamelCase to snake_case
        import re
        snake_case = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', class_name)
        return snake_case.lower()

    def _usage_tokens(self, usage: Optional[Dict[str, Any]]) -> Optional[Dict[str, int]]:
        """Normalize token counts across providers."""
        if not usage:
            return None

        # Try multiple keys for input tokens
        input_keys = ["input_tokens", "prompt_tokens", "promptTokenCount", "prompt_eval_count"]
        output_keys = ["output_tokens", "completion_tokens", "candidatesTokenCount", "eval_count"]

        input_tokens = self._first_integer(usage, *input_keys)
        output_tokens = self._first_integer(usage, *output_keys)

        if input_tokens is None and output_tokens is None:
            return None

        return {
            "input": input_tokens,
            "output": output_tokens
        }

    def _first_integer(self, hash: Dict[str, Any], *keys: str) -> Optional[int]:
        """Find first matching integer value from multiple possible keys."""
        for key in keys:
            # Try both string and symbol-like access patterns
            value = hash.get(key) or hash.get(key)
            if value is not None:
                try:
                    return int(value)
                except (ValueError, TypeError):
                    continue
        return None

    def _estimate_cost(
        self, backend: Optional[Base], tokens: Optional[Dict[str, int]]
    ) -> Optional[float]:
        """Calculate USD cost estimate."""
        if not backend or not hasattr(backend, 'estimate_cost'):
            return None
        if not tokens or tokens.get("input") is None or tokens.get("output") is None:
            return None

        return backend.estimate_cost(
            input_tokens=tokens["input"],
            output_tokens=tokens["output"]
        )
