# Python Port Plan: 06_the_logger (Ruby → Python)

## Overview

This plan outlines the port of Boukensha `06_the_logger` from Ruby to Python. This step introduces **structured logging** with session-based JSONL files, token usage tracking, and cost estimation for all LLM API calls.

**Estimated Effort:** 4-6 hours
**New Lines of Code:** ~200 lines (Logger class + Agent integration + Backend updates)

## What's New in 06_the_logger

The logger step adds comprehensive observability to the agent framework:

1. **Session-based Logging**: Every run creates a unique session file at `.boukensha/sessions/<session-id>.jsonl`
2. **Structured Events**: JSON Lines format logs all agent activities (iterations, prompts, tool calls, responses)
3. **Cost Tracking**: Token usage and USD cost estimation based on model pricing
4. **Debug Mode**: Optional raw API response logging via `Boukensha.debug!`
5. **Module-level State**: Debug/quiet flags and shared config accessor

---

## Scope

**Source:** `week1_baseline/ruby/06_the_logger/`
**Target:** `week1_baseline/python/06_the_logger/`

**Base:** Copy from `python/05_agent_loop/` and add logging capabilities

---

## File-by-File Mapping

| Ruby File | Python File | Lines | Status | Notes |
|-----------|-------------|-------|--------|-------|
| **NEW FILES** | | | | |
| `lib/boukensha/logger.rb` | `boukensha/logger.py` | 144 | **NEW** | Core logging implementation |
| **MODIFIED FILES** | | | | |
| `lib/boukensha.rb` | `boukensha/__init__.py` | ~30 | **UPDATE** | Add module state (debug/quiet/config) |
| `lib/boukensha/agent.rb` | `boukensha/agent.py` | ~250 | **UPDATE** | Integrate logger throughout |
| `lib/boukensha/backends/base.rb` | `boukensha/backends/base.py` | ~220 | **UPDATE** | Add cost estimation methods |
| `examples/example.rb` | `examples/example.py` | ~140 | **UPDATE** | Port with logger |
| **UNCHANGED** | | | | |
| All other files | Copy from 05_agent_loop | - | **COPY** | Client, Config, Context, etc. |

**Total New/Modified Lines:** ~200 lines

---

## New Component: Logger Class

### Logger Class (`boukensha/logger.py`)

The Logger class handles all structured logging to JSONL files.

**Core Responsibilities:**
- Session ID generation: `YYYYMMDDTHHMMSSZ-{8char-hex}`
- JSONL file management: `.boukensha/sessions/<session_id>.jsonl`
- Event serialization with timestamps (ISO8601)
- Cost/usage metadata extraction

**Public Methods:**
```python
class Logger:
    def __init__(self, session_id: Optional[str] = None) -> None:
        """Initialize logger with optional session ID."""

    def iteration(self, n: int, max: int) -> None:
        """Log iteration counter."""

    def limit_reached(self, kind: str, n: int, max: int) -> None:
        """Log when limits are reached (max_iterations, etc.)."""

    def turn_end(self, reason: str, iterations: int, tokens: Optional[Dict[str, int]] = None) -> None:
        """Log turn completion with summary stats."""

    def prompt(self, messages: List[Message], tools: Dict[str, Tool]) -> None:
        """Log messages and tools sent to API."""

    def tool_call(self, name: str, args: Dict[str, Any]) -> None:
        """Log tool invocation."""

    def tool_result(self, name: str, result: Any, ok: bool = True, error: Optional[str] = None) -> None:
        """Log tool execution result."""

    def response(
        self,
        text: str,
        usage: Optional[Dict[str, Any]],
        stop_reason: str,
        task: type,
        backend: Base
    ) -> None:
        """Log model response with metadata."""

    def raw(self, data: Dict[str, Any]) -> None:
        """Log raw API response (debug mode only)."""
```

**Private Methods:**
```python
    def _write_log(self, event: Dict[str, Any]) -> None:
        """Write JSON event to log file with session_id and timestamp."""

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""

    def _serialize_message(self, msg: Message) -> Dict[str, Any]:
        """Convert Message to loggable dict."""

    def _execution_metadata(
        self, task: type, backend: Base, usage: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract execution metadata (tokens, cost, model info)."""

    def _usage_tokens(self, usage: Optional[Dict[str, Any]]) -> Optional[Dict[str, int]]:
        """Normalize token counts across providers."""

    def _first_integer(self, hash: Dict[str, Any], *keys: str) -> Optional[int]:
        """Find first matching integer value from multiple possible keys."""

    def _estimate_cost(
        self, backend: Base, tokens: Optional[Dict[str, int]]
    ) -> Optional[float]:
        """Calculate USD cost estimate."""
```

### Session ID Format

```python
# Format: YYYYMMDDTHHMMSSZ-HHHHHHHH
# Example: 20260125T143022Z-a3b7c1f9

from datetime import datetime
import secrets

def _generate_session_id() -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    random_hex = secrets.token_hex(4)
    return f"{timestamp}-{random_hex}"
```

### JSONL File Format

Each line in `.boukensha/sessions/<session-id>.jsonl` is a complete JSON object:

```jsonl
{"session_id":"20260125T143022Z-a3b7c1f9","timestamp":"2026-01-25T14:30:22.123Z","event":"iteration","iteration":1,"max_iterations":25}
{"session_id":"20260125T143022Z-a3b7c1f9","timestamp":"2026-01-25T14:30:22.234Z","event":"prompt","messages":[...],"tools":[...]}
{"session_id":"20260125T143022Z-a3b7c1f9","timestamp":"2026-01-25T14:30:23.456Z","event":"response","text":"...","usage":{"input":385,"output":67},"cost_usd":0.000442,"model":"claude-haiku-4-5","provider":"anthropic"}
{"session_id":"20260125T143022Z-a3b7c1f9","timestamp":"2026-01-25T14:30:23.567Z","event":"tool_call","name":"read_file","args":{"path":"README.md"}}
{"session_id":"20260125T143022Z-a3b7c1f9","timestamp":"2026-01-25T14:30:23.678Z","event":"tool_result","name":"read_file","ok":true,"result":"# README..."}
{"session_id":"20260125T143022Z-a3b7c1f9","timestamp":"2026-01-25T14:30:24.789Z","event":"turn_end","reason":"end_turn","iterations":2,"total_tokens":{"input":450,"output":89},"total_cost_usd":0.000895}
```

### Usage Token Normalization

Different providers use different keys for token counts. The logger normalizes these:

```python
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
        "input": input_tokens or 0,
        "output": output_tokens or 0
    }
```

### Cost Estimation

```python
def _estimate_cost(
    self, backend: Base, tokens: Optional[Dict[str, int]]
) -> Optional[float]:
    """Calculate USD cost estimate."""
    if not tokens or not hasattr(backend, 'estimate_cost'):
        return None

    return backend.estimate_cost(
        input_tokens=tokens.get("input", 0),
        output_tokens=tokens.get("output", 0)
    )
```

---

## Module-Level State Updates

### Updated `boukensha/__init__.py`

```python
"""
Boukensha: AI-driven MUD player agent framework.

This module provides structured logging, tool dispatch, multi-provider
LLM integration, and agent loop for building autonomous MUD players.
"""

from boukensha.config import Config
from boukensha.context import Context
from boukensha.errors import UnknownToolError, UnsupportedModelError, ApiError, LoopError
from boukensha.message import Message
from boukensha.registry import Registry
from boukensha.tool import Tool
from boukensha.tasks.player import Player
from boukensha.prompt_builder import PromptBuilder
from boukensha.client import Client
from boukensha.agent import Agent
from boukensha.logger import Logger  # NEW
from boukensha import backends

__all__ = [
    "Config",
    "Context",
    "Message",
    "Registry",
    "Tool",
    "UnknownToolError",
    "UnsupportedModelError",
    "ApiError",
    "LoopError",
    "Player",
    "PromptBuilder",
    "Client",
    "Agent",
    "Logger",  # NEW
    "backends",
]

__version__ = "0.6.0"

# Module-level state (NEW)
_quiet = False
_debug = False
_config = None


def quiet() -> None:
    """Enable quiet mode (suppress console output)."""
    global _quiet
    _quiet = True


def loud() -> None:
    """Disable quiet mode (enable console output)."""
    global _quiet
    _quiet = False


def is_quiet() -> bool:
    """Check if quiet mode is enabled."""
    return _quiet


def debug() -> None:
    """Enable debug mode (log raw API responses)."""
    global _debug
    _debug = True


def is_debug() -> bool:
    """Check if debug mode is enabled."""
    return _debug


def config() -> Config:
    """Get or create the global Config singleton."""
    global _config
    if _config is None:
        _config = Config()
    return _config
```

---

## Agent Integration Updates

### Updated `boukensha/agent.py`

**Constructor Changes:**

```python
def __init__(
    self,
    context: Context,
    registry: Registry,
    builder: PromptBuilder,
    client: Client,
    task_settings: Optional[Dict[str, Any]] = None,
    max_iterations: Optional[int] = None,
    max_output_tokens: Optional[int] = None,
    logger: Optional[Logger] = None,  # NEW parameter
) -> None:
    """Initialize the agent."""
    self._context = context
    self._registry = registry
    self._builder = builder
    self._client = client
    self._max_iterations = self._resolve_max_iterations(task_settings, max_iterations)
    self._max_output_tokens = self._resolve_max_output_tokens(task_settings, max_output_tokens)
    self._iteration = 0
    self._logger = logger or Logger()  # NEW: Default logger instance
```

**New Methods:**

```python
def _log_response(self, text: str, response: Dict[str, Any]) -> None:
    """Log model response with usage metadata."""
    usage = self._normalized_usage(response)
    self._logger.response(
        text=text,
        usage=usage,
        stop_reason=self._builder.parse_response(response)["stop_reason"],
        task=self._context.task,
        backend=self._builder.backend
    )

def _normalized_usage(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize usage data across provider formats."""
    # Try multiple response formats
    if "usage" in response:
        return response["usage"]
    elif "metadata" in response and "usage" in response["metadata"]:
        return response["metadata"]["usage"]
    return None
```

**Updated `run()` Loop:**

```python
def run(self) -> str:
    """Run the agent loop until completion."""
    while True:
        # Check iteration limit
        if self._iteration_limit_reached():
            self._logger.limit_reached(
                kind="max_iterations",
                n=self._iteration,
                max=self._max_iterations
            )
            return self._wrap_up("max_iterations")

        self._iteration += 1
        self._logger.iteration(n=self._iteration, max=self._max_iterations)

        # Log prompt before API call
        self._logger.prompt(
            messages=self._context.messages,
            tools=self._context.tools
        )

        # Make API call
        response = self._client.call(**self._call_opts())

        # Log raw response if debug mode
        if __import__('boukensha').is_debug():
            self._logger.raw(data=response)

        parsed = self._builder.parse_response(response)

        # Check stop reason
        if parsed["stop_reason"] == "tool_use":
            self._handle_tool_calls(parsed["content"], response)
        else:
            text = self._extract_text(parsed["content"])
            self._log_response(text=text, response=response)

            # Log turn end
            self._logger.turn_end(
                reason="end_turn",
                iterations=self._iteration,
                tokens=None  # Could aggregate here
            )
            return text
```

**Updated `_handle_tool_calls()`:**

```python
def _handle_tool_calls(
    self, content: List[Dict[str, Any]], response: Dict[str, Any]
) -> None:
    """Handle tool use blocks by dispatching and injecting results."""
    # Extract and log reasoning text (if present)
    reasoning_blocks = [b for b in content if b.get("type") == "text"]
    if reasoning_blocks:
        reasoning_text = "".join(b.get("text", "") for b in reasoning_blocks)
        self._log_response(text=reasoning_text, response=response)

    # Add assistant message with tool use blocks
    self._context.add_message("assistant", content)

    # Dispatch each tool call
    for block in content:
        if block.get("type") == "tool_use":
            name = block["name"]
            args = block["input"]
            use_id = block["id"]

            # Log tool call
            self._logger.tool_call(name=name, args=args)

            # Execute tool with error handling
            try:
                result = self._registry.dispatch(name, args)
                self._logger.tool_result(name=name, result=str(result), ok=True)
                self._context.add_message("tool_result", str(result), tool_use_id=use_id)
            except Exception as e:
                error_msg = f"{e.__class__.__name__}: {e}"
                self._logger.tool_result(name=name, result="", ok=False, error=error_msg)
                # Re-raise to maintain existing error handling behavior
                raise
```

**Updated `_wrap_up()`:**

```python
def _wrap_up(self, reason: str) -> str:
    """Make a final wind-down call without tools."""
    self._context.add_message("user", self.WRAP_UP_DIRECTIVE)

    try:
        response = self._client.call(tools=[], max_output_tokens=self.WRAP_UP_OUTPUT_TOKENS)
        parsed = self._builder.parse_response(response)
        text = self._extract_text(parsed["content"])

        # Log wrap-up response
        self._log_response(text=text, response=response)

        # Log turn end
        self._logger.turn_end(reason=reason, iterations=self._iteration)

        return text if text.strip() else self._fallback_message(reason)
    except ApiError as e:
        # Still log turn end even on error
        self._logger.turn_end(reason=f"error:{reason}", iterations=self._iteration)
        return self._fallback_message(reason)
```

---

## Backend Base Class Updates

### Updated `boukensha/backends/base.py`

Add cost estimation methods:

```python
@property
def usage_unit(self) -> str:
    """Get the usage unit (e.g., 'tokens', 'characters')."""
    return self._model_info.get("usage_unit", "tokens")

@property
def usage_level(self) -> Optional[str]:
    """Get the usage level if defined (e.g., 'tier1', 'tier2')."""
    return self._model_info.get("usage_level")

def estimate_cost(self, input_tokens: int, output_tokens: int) -> Optional[float]:
    """
    Estimate the cost of a request in USD.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Estimated cost in USD, or None if pricing unavailable
    """
    try:
        input_cost = input_tokens * self.input_token_cost_per_million
        output_cost = output_tokens * self.output_token_cost_per_million
        return (input_cost + output_cost) / 1_000_000.0
    except (KeyError, TypeError):
        return None
```

**Note:** All backend MODELS dictionaries already include `cost_per_million` and `usage_unit` from the 05_agent_loop port, so no backend-specific changes are needed.

---

## Implementation Phases

### Phase 1: Logger Class (2 hours)

**Steps:**
1. Create `python/06_the_logger/boukensha/logger.py`
2. Implement session ID generation with `secrets.token_hex(4)`
3. Implement file I/O to `.boukensha/sessions/<session-id>.jsonl`
4. Implement all public logging methods
5. Implement private helper methods:
   - `_write_log()` - JSON serialization + file append
   - `_serialize_message()` - Message to dict conversion
   - `_usage_tokens()` - Token normalization
   - `_estimate_cost()` - Cost calculation
   - `_execution_metadata()` - Metadata extraction
6. Handle directory creation (`Path.mkdir(parents=True, exist_ok=True)`)
7. Use `json.dumps()` + `\n` for JSONL format
8. Add file flushing for immediate writes

**Reference:**
- `ruby/06_the_logger/lib/boukensha/logger.rb` (144 lines)

**Validation:**
- Session ID format matches: `YYYYMMDDTHHMMSSZ-{8hex}`
- JSONL files created in `.boukensha/sessions/`
- Each line is valid JSON with `session_id` and `timestamp`

---

### Phase 2: Module-Level State (30 min)

**Steps:**
1. Update `python/06_the_logger/boukensha/__init__.py`
2. Add module-level variables: `_quiet`, `_debug`, `_config`
3. Add module functions: `quiet()`, `loud()`, `is_quiet()`, `debug()`, `is_debug()`, `config()`
4. Export `Logger` in `__all__`
5. Update `__version__` to `"0.6.0"`

**Validation:**
- `import boukensha; boukensha.debug()` sets debug flag
- `boukensha.is_debug()` returns correct state
- `boukensha.config()` returns singleton Config instance

---

### Phase 3: Backend Updates (15 min)

**Steps:**
1. Copy `python/05_agent_loop/boukensha/backends/` to `python/06_the_logger/boukensha/backends/`
2. Update `base.py` with cost estimation methods (already done in 05)
3. Verify all backend MODELS include `cost_per_million` and `usage_unit`

**Validation:**
- `backend.estimate_cost(input_tokens=385, output_tokens=67)` returns float
- `backend.usage_unit` returns "tokens"

---

### Phase 4: Agent Integration (2 hours)

**Steps:**
1. Copy `python/05_agent_loop/boukensha/agent.py` to `python/06_the_logger/boukensha/agent.py`
2. Add `logger` parameter to `__init__()`
3. Add `_log_response()` method
4. Add `_normalized_usage()` method
5. Update `run()` loop:
   - Add `logger.iteration()` call
   - Add `logger.prompt()` before API call
   - Add `logger.raw()` for debug mode
   - Add `logger.turn_end()` on completion
6. Update `_handle_tool_calls()`:
   - Extract and log reasoning text
   - Add `logger.tool_call()` before dispatch
   - Wrap dispatch in try/except
   - Add `logger.tool_result()` with ok/error
7. Update `_wrap_up()`:
   - Log final response
   - Log turn_end even on error

**Validation:**
- Agent runs create session files
- All events logged in correct format
- Tool errors logged with `ok: false`
- Cost estimation appears in response events

---

### Phase 5: Copy Remaining Files (30 min)

**Steps:**
1. Copy all other files from `python/05_agent_loop/` unchanged:
   - `boukensha/client.py`
   - `boukensha/config.py`
   - `boukensha/context.py`
   - `boukensha/errors.py`
   - `boukensha/message.py`
   - `boukensha/prompt_builder.py`
   - `boukensha/registry.py`
   - `boukensha/tool.py`
   - `boukensha/tasks/`
2. Copy `prompts/system.md`
3. Copy `requirements.txt`

---

### Phase 6: Example and Testing (1 hour)

**Steps:**
1. Port `examples/example.rb` to `examples/example.py`
2. Add logger instantiation
3. Test with real API call
4. Verify session file created
5. Inspect JSONL output format
6. Test debug mode: `import boukensha; boukensha.debug()`
7. Test quiet mode: `boukensha.quiet()`

**Example Code:**

```python
#!/usr/bin/env python3
import os
from pathlib import Path
from boukensha import (
    Config, Context, Registry, Player,
    PromptBuilder, Client, Agent, Logger,
    backends
)

# Enable debug mode to log raw responses
import boukensha
boukensha.debug()

# Setup config
config = boukensha.config()  # Use module singleton
player_settings = config.tasks("player")
system_prompt = Player.system_prompt(
    player_settings,
    user_prompts_dir=config.user_prompts_dir,
    default_prompts_dir=Config.PROMPTS_DIR
)

# Create logger
logger = Logger()  # Generates session ID automatically
print(f"Session ID: {logger.session_id}")
print(f"Log file: {logger.log_file}")

# Create context and agent
ctx = Context(task=Player, system=system_prompt)
registry = Registry(ctx)

# Setup backend
provider = Player.provider(player_settings)
model = Player.model(player_settings)
backend = backends.Anthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    model=model
)

builder = PromptBuilder(context=ctx, backend=backend)
client = Client(builder)
agent = Agent(
    context=ctx,
    registry=registry,
    builder=builder,
    client=client,
    task_settings=player_settings,
    logger=logger  # Pass logger to agent
)

# Register tools
def read_file(path: str) -> str:
    with open(Path(__file__).parent.parent / path) as f:
        return f.read()

registry.tool(
    name="read_file",
    description="Read file contents",
    parameters={"path": {"type": "string"}},
    block=read_file
)

# Run agent
ctx.add_message("user", "Read README.md and summarize.")
result = agent.run()

print(f"\n=== RESULT ===\n{result}")
print(f"\nSession log: {logger.log_file}")
```

**Validation:**
- Session file created at `.boukensha/sessions/<session-id>.jsonl`
- File contains valid JSONL with all events
- Cost estimates present in response events
- Raw API responses logged in debug mode
- No console output in quiet mode

---

### Phase 7: Documentation (30 min)

**Steps:**
1. Create comprehensive `README.md`
2. Document Logger API
3. Document debug/quiet modes
4. Provide JSONL format examples
5. Add cost tracking examples

---

## Python Libraries

**Standard Library (No External Dependencies):**
- `json` - JSONL serialization
- `pathlib.Path` - File path handling
- `datetime` - ISO8601 timestamps (`datetime.utcnow().isoformat() + "Z"`)
- `secrets` - Cryptographically secure random hex (`secrets.token_hex(4)`)
- `typing` - Type hints

**Already Required (from 05_agent_loop):**
- `PyYAML` - Config loading
- `python-dotenv` - Environment variables

---

## Key Translation Patterns

### 1. Ruby Time → Python datetime

```ruby
# Ruby
Time.now.utc.iso8601
```

```python
# Python
from datetime import datetime
datetime.utcnow().isoformat() + "Z"
```

### 2. Ruby SecureRandom → Python secrets

```ruby
# Ruby
require 'securerandom'
SecureRandom.hex(4)
```

```python
# Python
import secrets
secrets.token_hex(4)
```

### 3. Ruby File.write (append mode) → Python Path

```ruby
# Ruby
File.open(log_file, 'a') do |f|
  f.puts(json_line)
  f.flush
end
```

```python
# Python
from pathlib import Path
with open(log_file, 'a') as f:
    f.write(json_line + '\n')
    f.flush()
```

### 4. Ruby Module Variables → Python Module Globals

```ruby
# Ruby
module Boukensha
  @debug = false

  def self.debug!
    @debug = true
  end

  def self.debug?
    @debug
  end
end
```

```python
# Python
# In boukensha/__init__.py
_debug = False

def debug() -> None:
    global _debug
    _debug = True

def is_debug() -> bool:
    return _debug
```

---

## Differences from Ruby

### 1. Session Directory Handling

**Ruby:** Uses `FileUtils.mkdir_p` (requires `require 'fileutils'`)
**Python:** Use `Path.mkdir(parents=True, exist_ok=True)` (stdlib)

### 2. Timestamp Format

**Ruby:** `Time.now.utc.iso8601` returns `"2026-01-25T14:30:22Z"`
**Python:** `datetime.utcnow().isoformat()` returns `"2026-01-25T14:30:22.123456"` - need to add `"Z"` suffix

### 3. JSON Serialization

**Ruby:** Can handle symbols, dates automatically
**Python:** Need explicit string conversion for non-JSON types

---

## Testing Strategy

### Manual Validation

1. Run example and verify session file created
2. Check JSONL format: `cat .boukensha/sessions/<session-id>.jsonl | jq`
3. Verify all event types present:
   - iteration
   - prompt
   - response
   - tool_call
   - tool_result
   - turn_end
   - raw (debug mode only)
4. Verify cost estimation:
   - Extract `cost_usd` from response events
   - Verify matches manual calculation
5. Test debug mode:
   - `boukensha.debug()`
   - Verify raw API responses logged
6. Test quiet mode:
   - `boukensha.quiet()`
   - Verify no console output

### Automated Validation

```python
# Test session ID format
import re
assert re.match(r'^\d{8}T\d{6}Z-[a-f0-9]{8}$', logger.session_id)

# Test file creation
assert Path(logger.log_file).exists()

# Test JSONL format
with open(logger.log_file) as f:
    for line in f:
        event = json.loads(line)
        assert 'session_id' in event
        assert 'timestamp' in event
        assert 'event' in event
```

---

## Timeline Estimate

- **Phase 1 (Logger):** 2 hours
- **Phase 2 (Module State):** 30 min
- **Phase 3 (Backends):** 15 min
- **Phase 4 (Agent):** 2 hours
- **Phase 5 (Copy Files):** 30 min
- **Phase 6 (Example/Testing):** 1 hour
- **Phase 7 (Documentation):** 30 min

**Total:** 6-8 hours

---

## Success Criteria

1. Logger creates session files in `.boukensha/sessions/`
2. All event types logged correctly
3. JSONL format valid (each line is complete JSON)
4. Cost estimation works across all providers
5. Debug mode logs raw API responses
6. Quiet mode suppresses console output
7. Tool errors logged with `ok: false`
8. Session ID format matches Ruby: `YYYYMMDDTHHMMSSZ-{8hex}`
9. Timestamps in ISO8601 format with Z suffix
10. Example runs successfully with real API

---

## Notes

- **No external dependencies** beyond what 05_agent_loop already requires
- **Session files are gitignored** - `.boukensha/` is in `.gitignore`
- **JSONL is human-readable** - can inspect with `cat` or `jq`
- **Cost estimates are approximate** - based on model pricing metadata
- **Debug mode is verbose** - logs full API responses (can be large)
- **Logger is optional** - Agent defaults to `Logger()` if not provided

---

## See Also

- Original Ruby implementation: `ruby/06_the_logger/`
- Previous Python port: `python/05_agent_loop/`
- Port plan example: `docs/plans/python_port/00_config`
