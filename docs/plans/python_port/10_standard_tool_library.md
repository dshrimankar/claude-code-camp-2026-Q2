# Python Port Plan: Step 10 - Standard Tool Library (MCP Host)

## Overview
This plan outlines the port of Step 10 from Ruby to Python. Step 10 represents a major architectural shift where Boukensha becomes a pure MCP (Model Context Protocol) host. All built-in tools are removed, and the agent gains its capabilities exclusively through external MCP servers configured in `settings.yaml`.

**Key Concept:** Tools are data, not code. By implementing the MCP protocol, Boukensha can host any MCP server through the same generic mechanism.

## Scope
Port **Step 10** from Ruby to Python:
- **Source:** `week1_baseline/ruby/10_standard_tool_library/`
- **Target:** `week1_baseline/python/10_standard_tool_library/`

**What's New in Step 10:**
1. **NEW:** MCP Client implementation (`lib/boukensha/mcp/client.rb`)
2. **NEW:** MCP Tools integration (`lib/boukensha/tools/mcp.rb`)
3. **NEW:** Three comprehensive test files for MCP functionality
4. **MODIFIED:** Config adds `mcp_servers()` method
5. **MODIFIED:** Main module adds `register_mcp_servers()` private method
6. **MODIFIED:** REPL shows MCP server status in banner
7. **MODIFIED:** Loader removes MUD-specific logic (tools come from config)
8. **MODIFIED:** Examples simplified (no tool registration needed)
9. **MODIFIED:** Documentation updated to explain MCP architecture

**What Was Removed:**
- No changes from step 09 (step 09 already removed built-in tools)
- This is purely additive: adds MCP host capability

## Target Directory Structure

```
week1_baseline/python/10_standard_tool_library/
  boukensha/
    __init__.py                 # MODIFIED: add register_mcp_servers()
    config.py                   # MODIFIED: add mcp_servers() method
    context.py                  # (no changes from step 09)
    message.py                  # (no changes from step 09)
    registry.py                 # (no changes from step 09)
    tool.py                     # (no changes from step 09)
    errors.py                   # (no changes from step 09)
    client.py                   # (no changes from step 09)
    agent.py                    # (no changes from step 09)
    logger.py                   # (no changes from step 09)
    prompt_builder.py           # (no changes from step 09)
    run_dsl.py                  # (no changes from step 09)
    repl.py                     # MODIFIED: add servers parameter & status
    mcp/                        # NEW: MCP protocol implementation
      __init__.py
      client.py                 # NEW: ~200 lines - MCP-over-stdio client
    tools/                      # NEW: MCP tools integration
      __init__.py
      mcp.py                    # NEW: ~150 lines - MCP host integration
    tasks/
      __init__.py
      base.py                   # (no changes from step 09)
      player.py                 # (no changes from step 09)
    backends/
      __init__.py
      base.py                   # (no changes from step 09)
      anthropic.py              # (no changes from step 09)
      openai.py                 # (no changes from step 09)
      gemini.py                 # (no changes from step 09)
      ollama.py                 # (no changes from step 09)
      ollama_cloud.py           # (no changes from step 09)
  prompts/
    system.md                   # MODIFIED: add auto-connection paragraph
  examples/
    example.py                  # MODIFIED: simplified (no tool registration)
    mcp_mud_demo.py             # NEW: dry-run and full agent demo
  tests/                        # NEW: comprehensive MCP test suite
    __init__.py
    test_helper.py              # NEW: McpTestHelper module
    test_mcp_client.py          # NEW: ~150 lines - MCP client tests
    test_tools_mcp.py           # NEW: ~200 lines - MCP tools tests
    test_mcp_servers_config.py  # NEW: ~250 lines - config & integration tests
  boukensha_loader.py           # MODIFIED: remove MUD-specific logic
  pyproject.toml                # MODIFIED: version 0.10.0
  README.md                     # MODIFIED: explain MCP architecture
```

---

## File-by-File Mapping

### New Files (Critical)

| Ruby File | Python File | Lines | Complexity | Priority | Notes |
|-----------|-------------|-------|------------|----------|-------|
| `lib/boukensha/mcp/client.rb` | `boukensha/mcp/client.py` | ~200 | High | **P0** | MCP-over-stdio client, subprocess mgmt |
| `lib/boukensha/tools/mcp.rb` | `boukensha/tools/mcp.py` | ~150 | Medium | **P0** | MCP tools registration & integration |
| `test/test_mcp_client.rb` | `tests/test_mcp_client.py` | ~150 | Medium | **P1** | Client tests (handshake, discovery, calling) |
| `test/test_tools_mcp.rb` | `tests/test_tools_mcp.py` | ~200 | Medium | **P1** | Tools tests (registration, prefix, collision) |
| `test/test_mcp_servers_config.rb` | `tests/test_mcp_servers_config.py` | ~250 | High | **P1** | Config & integration tests |
| `test/helper.rb` | `tests/test_helper.py` | ~80 | Low | **P1** | McpTestHelper module, FakeMud |
| `examples/mcp_mud_demo.rb` | `examples/mcp_mud_demo.py` | ~100 | Low | **P2** | Dry-run and full agent demo |

### Modified Files

| Ruby File | Python File | Changes | Complexity | Priority | Notes |
|-----------|-------------|---------|------------|----------|-------|
| `lib/boukensha/config.rb` | `boukensha/config.py` | Add `mcp_servers()` method | Low | **P0** | ~30 lines added |
| `lib/boukensha.rb` | `boukensha/__init__.py` | Add `register_mcp_servers()` | Medium | **P0** | ~40 lines added |
| `lib/boukensha/repl.rb` | `boukensha/repl.py` | Add servers param & status | Low | **P0** | ~20 lines added |
| `lib/boukensha_loader.rb` | `boukensha_loader.py` | Remove MUD env vars | Low | **P0** | ~10 lines removed |
| `examples/example.rb` | `examples/example.py` | Simplify (no tools) | Low | **P2** | ~5 lines removed |
| `prompts/system.md` | `prompts/system.md` | Add auto-connection note | Low | **P2** | ~1 paragraph added |
| `README.md` | `README.md` | Explain MCP architecture | Low | **P2** | Documentation |

**Total New Lines:** ~800 lines (excluding tests/docs)
**Total Modified Lines:** ~100 lines

---

## Dependencies

### Python Standard Library
- `subprocess` - Spawn MCP servers (equivalent to Ruby `Open3.popen3`)
- `json` - JSON-RPC 2.0 protocol (equivalent to Ruby `JSON`)
- `atexit` - Cleanup hooks (equivalent to Ruby `at_exit`)
- `sys` - Python executable path (equivalent to Ruby `RbConfig.ruby`)
- `threading` - For thread-safe readline operations
- `io` - Text I/O wrappers for subprocess pipes

### External Dependencies (Existing)
- `PyYAML` - YAML parsing (for config)
- `python-dotenv` - .env file loading
- `requests` - HTTP client (for LLM APIs)

### External Dependencies (New)
- **None** - MCP client uses only stdlib

### Test Dependencies
- `pytest` - Test framework (recommended)
- Access to `mud-manager --mcp` executable (for testing)

---

## Key Translation Patterns

### 1. Ruby `Open3.popen3` → Python `subprocess.Popen`

```ruby
# Ruby
stdin, stdout, stderr, wait = Open3.popen3(env, *cmd)
```

```python
# Python
import subprocess

proc = subprocess.Popen(
    cmd,
    env=env,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=False  # Binary mode for line-delimited JSON
)
# Use io.TextIOWrapper for line-buffered text I/O
import io
stdout_text = io.TextIOWrapper(proc.stdout, encoding='utf-8', line_buffering=True)
stdin_text = io.TextIOWrapper(proc.stdin, encoding='utf-8', line_buffering=True)
```

### 2. JSON-RPC Request/Response

```ruby
# Ruby - write JSON line
@stdin.puts(JSON.generate(payload))
@stdin.flush

# Read JSON line
line = @stdout.gets
response = JSON.parse(line)
```

```python
# Python - write JSON line
import json
json_line = json.dumps(payload) + '\n'
self.stdin.write(json_line)
self.stdin.flush()

# Read JSON line
line = self.stdout.readline()
response = json.loads(line)
```

### 3. Subprocess Cleanup with `atexit`

```ruby
# Ruby
at_exit do
  client.close
end
```

```python
# Python
import atexit

def cleanup():
    client.close()

atexit.register(cleanup)
```

### 4. Schema Conversion (MCP → Boukensha)

```ruby
# Ruby - convert MCP inputSchema to Boukensha params
def to_boukensha_params(input_schema)
  properties = input_schema["properties"] || {}
  properties.each_with_object({}) do |(name, schema), result|
    result[name.to_sym] = {
      type: schema["type"],
      description: with_enum(schema)
    }
  end
end
```

```python
# Python - convert MCP inputSchema to Boukensha params
def to_boukensha_params(input_schema: dict) -> dict:
    properties = input_schema.get("properties", {})
    result = {}
    for name, schema in properties.items():
        result[name] = {
            "type": schema["type"],
            "description": with_enum(schema)
        }
    return result
```

### 5. Client-Side Name Prefixing

```ruby
# Ruby
def self.prefixed(name, prefix)
  return name unless prefix
  "#{prefix}__#{name}"
end
```

```python
# Python
@staticmethod
def prefixed(name: str, prefix: Optional[str]) -> str:
    if not prefix:
        return name
    return f"{prefix}__{name}"
```

### 6. Collision Detection

```ruby
# Ruby
existing = registry.tool_names
if existing.include?(tool_name)
  raise CollisionError, "MCP tool name collision on '#{tool_name}'"
end
```

```python
# Python
existing = registry.tool_names() if hasattr(registry, 'tool_names') else []
if tool_name in existing:
    raise CollisionError(
        f"MCP tool name collision on '{tool_name}' — "
        f"a tool by that name is already registered. "
        f"Give this server a distinct `prefix:` in mcp_servers."
    )
```

---

## Phase 1: Port MCP Client

**Priority:** HIGH (P0)
**Estimated Time:** 3-4 hours

### Steps:

1. **Create directory structure**
   ```bash
   mkdir -p boukensha/mcp
   touch boukensha/mcp/__init__.py
   ```

2. **Port `boukensha/mcp/client.py`** (~200 lines)
   - Import: `subprocess`, `json`, `io`, `sys`, `typing`
   - Define `McpClient` class
   - **Key methods to port:**
     - `__init__(self, process, stdin, stdout)`
     - `spawn(command: str, args: List[str], env: Dict[str, str])` - Class method factory
     - `call_tool(name: str, arguments: dict) -> dict` - Returns `{"text": str, "error": bool}`
     - `close()` - Clean shutdown with `proc.terminate()` and `proc.wait()`
     - Private helpers:
       - `_handshake()` - Initialize protocol
       - `_fetch_tools()` - Discover tools via `tools/list`
       - `_request(method: str, params: dict)` - JSON-RPC request
       - `_notify(method: str, params: dict)` - JSON-RPC notification (no response)
       - `_write(payload: dict)` - Write JSON line
       - `_read_until(match_fn: Callable)` - Read until predicate matches

   - **Protocol details:**
     - Version: `"2025-06-18"`
     - Handshake sequence:
       1. Send `initialize` request with `protocolVersion` and `capabilities: {}`
       2. Wait for `initialize` response
       3. Send `notifications/initialized` notification
     - Tool discovery: Send `tools/list` request
     - Tool calling: Send `tools/call` with `name` and `arguments`
     - Content extraction: Get first "text" type content block, ignore others

   - **Error handling:**
     - Subprocess spawn failure: Raise `RuntimeError` with stderr
     - JSON parse errors: Raise with context
     - Tool execution errors: Return `{"text": error_msg, "error": True}`

3. **Add error class to `boukensha/errors.py`**
   ```python
   class CollisionError(Exception):
       """Raised when MCP tool names collide."""
       pass
   ```

4. **Update `boukensha/mcp/__init__.py`**
   ```python
   from boukensha.mcp.client import McpClient

   __all__ = ["McpClient"]
   ```

**Reference Files:**
- `week1_baseline/ruby/10_standard_tool_library/lib/boukensha/mcp/client.rb` (200 lines)

**Validation:**
- Can spawn `mud-manager --mcp` successfully
- Can complete handshake and get server info
- Can discover tools via `tools/list`
- Can call a tool and get response
- Handles tool errors correctly (isError flag)
- Raises error when spawning nonexistent command

---

## Phase 2: Port MCP Tools Integration

**Priority:** HIGH (P0)
**Estimated Time:** 2-3 hours

### Steps:

1. **Create directory structure**
   ```bash
   mkdir -p boukensha/tools
   touch boukensha/tools/__init__.py
   ```

2. **Port `boukensha/tools/mcp.py`** (~150 lines)
   - Import: `atexit`, `typing`, `CollisionError`, `McpClient`
   - **Key functions to port:**
     - `register(registry, command: str, args: List[str] = None, env: Dict[str, str] = None, prefix: str = None) -> None`
       - Spawns MCP server
       - Registers all tools
       - Sets up cleanup hook
     - `register_client(registry, client: McpClient, prefix: str = None) -> int`
       - Registers tools from pre-spawned client
       - Returns tool count
       - Main registration logic
     - `prefixed(name: str, prefix: Optional[str]) -> str`
       - Apply prefix with `__` separator
     - `to_boukensha_params(input_schema: dict) -> dict`
       - Convert MCP schema to Boukensha format
     - `with_enum(schema: dict) -> str`
       - Append enum values to description

   - **Registration logic:**
     1. Check for collisions with existing tools (via `registry.tool_names()`)
     2. For each tool from `client.tools`:
        - Apply prefix to name
        - Convert MCP `inputSchema` to Boukensha parameters
        - Register with registry
        - Capture client and remote name in closure
     3. Return tool count for logging

   - **Tool execution wrapper:**
     ```python
     def tool_impl(**kwargs):
         # Convert symbol-keyed kwargs to string keys
         str_kwargs = {str(k): v for k, v in kwargs.items()}
         result = client.call_tool(remote_name, str_kwargs)
         if result.get("error"):
             return f"Error: {result['text']}"
         return result["text"]
     ```

3. **Update `boukensha/tools/__init__.py`**
   ```python
   from boukensha.tools import mcp

   __all__ = ["mcp"]
   ```

4. **Update `boukensha/errors.py`**
   - Ensure `CollisionError` is exported in `__all__`

**Reference Files:**
- `week1_baseline/ruby/10_standard_tool_library/lib/boukensha/tools/mcp.rb` (150 lines)

**Validation:**
- Can register MCP server and discover all tools
- Prefix is applied correctly to tool names
- Collision detection works (both MCP-to-MCP and MCP-to-local)
- Schema conversion handles enums correctly
- Tool execution works end-to-end
- Cleanup happens on exit

---

## Phase 3: Modify Config for MCP Servers

**Priority:** HIGH (P0)
**Estimated Time:** 1-2 hours

### Steps:

1. **Port `mcp_servers()` method to `boukensha/config.py`** (~30 lines)
   ```python
   def mcp_servers(self) -> Dict[str, Dict[str, Any]]:
       """Parse and normalize mcp_servers configuration.

       Returns dict: {
           "server_name": {
               "command": str,
               "args": List[str],
               "env": Dict[str, str],
               "prefix": Optional[str],
               "required": bool
           }
       }
       """
       raw = self.dig("mcp_servers") or {}
       result = {}

       for name, config in raw.items():
           if not isinstance(config, dict):
               continue

           # Normalize config with defaults
           normalized = {
               "command": str(config.get("command", "")),
               "args": [str(arg) for arg in config.get("args", [])],
               "env": {str(k): str(v) for k, v in config.get("env", {}).items()},
               "prefix": str(config["prefix"]) if config.get("prefix") else None,
               "required": config.get("required", True)
           }

           result[str(name)] = normalized

       return result
   ```

2. **Add property for backward compatibility (optional)**
   ```python
   @property
   def has_mcp_servers(self) -> bool:
       """Check if any MCP servers are configured."""
       return bool(self.mcp_servers())
   ```

**Reference Files:**
- `week1_baseline/ruby/10_standard_tool_library/lib/boukensha/config.rb` (lines 68-95)

**Validation:**
- Parses `mcp_servers:` block from settings.yaml
- Applies correct defaults: `args: []`, `env: {}`, `prefix: None`, `required: True`
- Stringifies all values (critical for subprocess)
- Returns empty dict when no servers configured

---

## Phase 4: Add MCP Server Registration to Main Module

**Priority:** HIGH (P0)
**Estimated Time:** 2 hours

### Steps:

1. **Add private `_register_mcp_servers()` function to `boukensha/__init__.py`** (~40 lines)
   ```python
   def _register_mcp_servers(registry, cfg: Config) -> Dict[str, int]:
       """Register all configured MCP servers.

       Args:
           registry: Tool registry (Registry or RunDSL)
           cfg: Config instance

       Returns:
           Dict mapping server name to tool count

       Raises:
           Exception: If required server fails to start
           CollisionError: If tool names collide (always fatal)
       """
       from boukensha.tools import mcp
       from boukensha.errors import CollisionError

       servers = cfg.mcp_servers()
       summary = {}

       for name, config in servers.items():
           is_required = config["required"]

           try:
               count = mcp.register(
                   registry,
                   command=config["command"],
                   args=config["args"],
                   env=config["env"],
                   prefix=config["prefix"]
               )
               summary[name] = count

           except CollisionError:
               # Collision is always fatal, even for optional servers
               raise

           except Exception as e:
               if is_required:
                   raise Exception(
                       f"MCP server '{name}' failed to start: {e}\n"
                       f"Check that '{config['command']}' is installed and working."
                   )
               else:
                   import boukensha
                   if not boukensha.is_quiet():
                       print(
                           f"Warning: optional MCP server '{name}' failed to start: {e}\n"
                           f"         Continuing without its tools.",
                           file=sys.stderr
                       )

       return summary
   ```

2. **Modify `run()` function** - Add MCP server registration
   ```python
   def run(...):
       # ... existing setup code ...

       # Create context and registry
       ctx = Context(task=task_class, system=system)
       registry = Registry(ctx)

       # Execute block with RunDSL if provided
       if block:
           dsl = RunDSL(registry)
           block(dsl)

       # NEW: Register MCP servers from config
       _register_mcp_servers(registry, cfg)

       # ... continue with backend, agent setup ...
   ```

3. **Modify `repl()` function** - Add MCP server registration and pass to REPL
   ```python
   def repl(...):
       # ... existing setup code ...

       # Create context and registry
       ctx = Context(task=task_class, system=system)
       registry = Registry(ctx)

       # Execute block with RunDSL if provided
       if block:
           dsl = RunDSL(registry)
           block(dsl)

       # NEW: Register MCP servers and get summary
       servers_summary = _register_mcp_servers(registry, cfg)

       # ... create builder, client, logger ...

       # Start the REPL with servers summary
       try:
           Repl(
               # ... existing params ...
               servers=servers_summary,  # NEW parameter
           ).start()
       # ... rest unchanged ...
   ```

**Reference Files:**
- `week1_baseline/ruby/10_standard_tool_library/lib/boukensha.rb` (lines 114-139, 208-211)

**Validation:**
- MCP servers are registered before agent starts
- Required servers cause fatal error if they fail
- Optional servers warn and continue if they fail
- Collision errors are never excused (even for optional servers)
- Server summary is passed to REPL

---

## Phase 5: Update REPL with Server Status

**Priority:** HIGH (P0)
**Estimated Time:** 1 hour

### Steps:

1. **Modify `boukensha/repl.py`** (~20 lines changed)

   - Add `servers` parameter to `__init__`:
     ```python
     def __init__(
         self,
         # ... existing parameters ...
         servers: Optional[Dict[str, int]] = None,  # NEW
     ):
         # ... existing init code ...
         self._servers = servers or {}
     ```

   - Add `_servers_status_string()` helper method:
     ```python
     def _servers_status_string(self) -> str:
         """Generate servers status line for banner.

         Returns:
             "mud (26)  filesystem (10)" or "(none configured)"
         """
         if not self._servers:
             return "(none configured — the agent has no tools)"

         parts = [f"{name} ({count})" for name, count in self._servers.items()]
         return "  ".join(parts)
     ```

   - Update `_banner()` method to include servers:
     ```python
     def _banner(self) -> str:
         # ... existing banner code ...

         # Add servers status line
         servers_status = self._servers_status_string()
         banner_lines.append(f"  servers:   {servers_status}")

         # ... rest of banner ...
     ```

**Reference Files:**
- `week1_baseline/ruby/10_standard_tool_library/lib/boukensha/repl.rb` (lines 17-19, 67-73, banner method)

**Validation:**
- REPL banner shows server status
- Shows `(none configured)` when no servers
- Shows `server_name (count)` for each configured server
- Multiple servers displayed with proper spacing

---

## Phase 6: Simplify Loader

**Priority:** HIGH (P0)
**Estimated Time:** 30 minutes

### Steps:

1. **Modify `boukensha_loader.py`** - Remove MUD-specific logic

   - Remove all environment variable handling for MUD_*
   - Loader just calls `boukensha.repl()` with no arguments
   - Tools now come from `mcp_servers:` in settings.yaml

   The `load_and_start_repl()` method should be simplified:
   ```python
   @classmethod
   def load_and_start_repl(cls):
       """Load the resolved boukensha module and start the REPL."""
       module_name, source_dir = cls.resolve()

       # Show debug info if requested
       if os.environ.get("BOUKENSHA_DEBUG"):
           if source_dir is None:
               print(f"[boukensha] loading bundled module", file=sys.stderr)
           else:
               print(f"[boukensha] loading from: {source_dir}", file=sys.stderr)

       # Import the resolved module
       try:
           import boukensha
       except ImportError as e:
           sys.exit(f"boukensha: failed to import: {e}")

       # Verify it has repl() method
       if not hasattr(boukensha, 'repl'):
           step_dir = source_dir if source_dir else "(bundled)"
           sys.exit(
               f"boukensha: the step at {step_dir}\n"
               f"       does not support the interactive REPL (added in step 7).\n"
               f"       Run its examples directly, e.g.:\n"
               f"         python {step_dir}/examples/*.py\n"
               f"       Or point BOUKENSHA_PATH at step 7 or later."
           )

       # Start the REPL - tools come from config now
       boukensha.repl()
   ```

**Reference Files:**
- `week1_baseline/ruby/10_standard_tool_library/lib/boukensha_loader.rb` (lines 76-94)

**Validation:**
- Loader still handles BOUKENSHA_PATH and BOUKENSHA_DIR
- No MUD-specific environment variables
- Just calls `boukensha.repl()` with no arguments
- Servers inherit boukensha's environment (so MUD_HOST etc. still work if in shell)

---

## Phase 7: Port Test Suite

**Priority:** MEDIUM (P1)
**Estimated Time:** 4-5 hours

### Steps:

1. **Create test directory structure**
   ```bash
   mkdir -p tests
   touch tests/__init__.py
   ```

2. **Port `tests/test_helper.py`** (~80 lines)
   - Define `McpTestHelper` class
   - Methods:
     - `start_fake_mud(port: int)` - Start FakeMud server
     - `fake_mud_env(port: int)` - Generate env dict for mud-manager
     - `mud_manager_command()` - Return command string
     - `mud_manager_args()` - Return args list
     - `config_from(yaml_str: str)` - Create temp config from YAML
   - Define `FakeMud` class (minimal telnet server for testing)

3. **Port `tests/test_mcp_client.py`** (~150 lines)
   - Test handshake and server info
   - Test tool discovery
   - Test tool calling with valid arguments
   - Test error handling (isError flag)
   - Test spawning nonexistent commands
   - Use pytest fixtures for setup/teardown

4. **Port `tests/test_tools_mcp.py`** (~200 lines)
   - Test registration from discovery
   - Test prefix application (client-side)
   - Test nil prefix (bare names)
   - Test enum in parameter descriptions
   - Test collision detection:
     - MCP-to-MCP collision
     - MCP-to-local collision
   - Verify server never sees prefix

5. **Port `tests/test_mcp_servers_config.py`** (~250 lines)
   - Test config parsing and defaults
   - Test required vs optional servers:
     - Required server failure → fatal
     - Optional server failure → warn and continue
   - Test collision handling (not excused by optional)
   - Test mud as "just another server"
   - Test tool count summary
   - Integration tests with real servers

**Reference Files:**
- `week1_baseline/ruby/10_standard_tool_library/test/helper.rb`
- `week1_baseline/ruby/10_standard_tool_library/test/test_mcp_client.rb`
- `week1_baseline/ruby/10_standard_tool_library/test/test_tools_mcp.rb`
- `week1_baseline/ruby/10_standard_tool_library/test/test_mcp_servers_config.rb`

**Test Dependencies:**
- `pytest` - Test framework
- `mud-manager` - Must be installed and accessible

**Validation:**
- All tests pass
- Tests can spawn `mud-manager --mcp`
- Collision detection works correctly
- Required vs optional server handling works
- Schema conversion is accurate

---

## Phase 8: Update Examples and Documentation

**Priority:** LOW (P2)
**Estimated Time:** 1-2 hours

### Steps:

1. **Simplify `examples/example.py`** (~5 lines removed)
   ```python
   #!/usr/bin/env python3
   """Simple example showing Boukensha with MCP servers from config."""

   import boukensha

   # Tools now come from mcp_servers: in settings.yaml
   # No manual tool registration needed!

   result = boukensha.run(
       task="Look around and tell me what you see"
   )

   print(f"\n{'='*50}")
   print(f"Agent response: {result}")
   print(f"{'='*50}")
   ```

2. **Port `examples/mcp_mud_demo.py`** (~100 lines)
   - Dry-run mode: Manually spawn daemon, register tools, test dispatch
   - Full mode: Uses config (identical to example.py)
   - Shows that MCP layer is server-agnostic

3. **Update `prompts/system.md`** - Add auto-connection paragraph
   ```markdown
   ## Current Status

   When you first start, you'll be **disconnected** from the MUD server.
   This is normal — you automatically connect when you perform your first
   game action (like `look` or `move`).
   ```

4. **Update `README.md`** - Explain MCP architecture
   - Document that Boukensha ships NO tools of its own
   - Explain what was removed (Tools::FileSystem, Tools::Shell, Tools::Mud)
   - Document trade-offs (needs npx for filesystem, etc.)
   - Show configuration format for `mcp_servers:`
   - List technical considerations

5. **Update `pyproject.toml`** - Bump version to 0.10.0
   ```toml
   [project]
   name = "boukensha"
   version = "0.10.0"
   description = "BOUKENSHA — a tiny teaching framework for coding harnesses"
   ```

**Reference Files:**
- `week1_baseline/ruby/10_standard_tool_library/examples/example.rb`
- `week1_baseline/ruby/10_standard_tool_library/examples/mcp_mud_demo.rb`
- `week1_baseline/ruby/10_standard_tool_library/prompts/system.md`
- `week1_baseline/ruby/10_standard_tool_library/README.md`

**Validation:**
- `example.py` runs successfully with config
- `mcp_mud_demo.py` shows both modes
- Documentation is clear and accurate
- Version is updated to 0.10.0

---

## Python 3.8 Compatibility Considerations

**Use:**
- `from __future__ import annotations` - for forward references
- `typing.Dict`, `typing.List`, `typing.Optional`, `typing.Callable` - not `dict`, `list`, `None | T`
- `typing.Union[X, Y]` - not `X | Y`
- `subprocess.Popen` with text=False (binary mode) + `io.TextIOWrapper`
- `atexit.register()` for cleanup hooks

**Avoid:**
- `match`/`case` statements (3.10+)
- `|` union operator for types (3.10+)
- `dict | dict` merge operator (3.9+) - use `{**d1, **d2}`
- `str.removeprefix`/`removesuffix` (3.9+)

**Special Considerations for MCP Client:**
- Use `text=False` with `subprocess.Popen` for binary mode
- Wrap with `io.TextIOWrapper(..., line_buffering=True)` for line-based I/O
- This ensures proper buffering behavior across Python versions

---

## Testing Strategy

### Unit Tests (pytest)

1. **MCP Client Tests** (`tests/test_mcp_client.py`)
   - Test handshake with real server
   - Test tool discovery returns expected tools
   - Test tool calling with valid arguments
   - Test error handling (isError flag in response)
   - Test subprocess cleanup

2. **MCP Tools Tests** (`tests/test_tools_mcp.py`)
   - Test registration creates correct tool signatures
   - Test prefix application (including nil prefix)
   - Test collision detection (fatal for all cases)
   - Test schema conversion (including enum handling)
   - Test tool execution end-to-end

3. **MCP Config Tests** (`tests/test_mcp_servers_config.py`)
   - Test config parsing with defaults
   - Test required vs optional server failure modes
   - Test collision not excused by optional flag
   - Test tool count summary
   - Integration test with real servers

### Manual Validation

1. **Basic REPL Test**
   ```bash
   cd week1_baseline/python/10_standard_tool_library
   python3 -c "import boukensha; boukensha.repl()"
   ```
   - Verify banner shows server status
   - Verify tools are available
   - Test a few tool calls manually

2. **Example Scripts**
   ```bash
   python3 examples/example.py
   python3 examples/mcp_mud_demo.py --dry
   python3 examples/mcp_mud_demo.py
   ```

3. **Configuration Testing**
   - Test with no `mcp_servers:` block (empty tools)
   - Test with required server that doesn't exist (should fail)
   - Test with optional server that doesn't exist (should warn)
   - Test with name collision (should fail)
   - Test with multiple servers and prefixes

### Cross-Version Compatibility

Test on multiple Python versions:
- Python 3.8 (minimum supported)
- Python 3.9
- Python 3.10+

---

## Migration Checklist

### Pre-Port
- [x] Analyze Ruby step 10 codebase structure
- [x] Research MCP protocol implementation
- [x] Identify all new components
- [x] Document translation patterns for subprocess management
- [x] Create comprehensive porting plan

### Core Implementation (P0)
- [ ] Copy step 09 to step 10 directory
- [ ] Create `boukensha/mcp/` directory structure
- [ ] Port `boukensha/mcp/client.py` (~200 lines)
- [ ] Add `CollisionError` to `boukensha/errors.py`
- [ ] Create `boukensha/tools/` directory structure
- [ ] Port `boukensha/tools/mcp.py` (~150 lines)
- [ ] Add `mcp_servers()` method to `boukensha/config.py`
- [ ] Add `_register_mcp_servers()` to `boukensha/__init__.py`
- [ ] Modify `run()` to register MCP servers
- [ ] Modify `repl()` to register MCP servers and pass summary
- [ ] Update `boukensha/repl.py` with servers parameter and status
- [ ] Simplify `boukensha_loader.py` (remove MUD env vars)

### Testing (P1)
- [ ] Create `tests/` directory structure
- [ ] Port `tests/test_helper.py` (McpTestHelper, FakeMud)
- [ ] Port `tests/test_mcp_client.py` (~150 lines)
- [ ] Port `tests/test_tools_mcp.py` (~200 lines)
- [ ] Port `tests/test_mcp_servers_config.py` (~250 lines)
- [ ] Run all tests with pytest
- [ ] Ensure `mud-manager --mcp` works for tests

### Examples & Documentation (P2)
- [ ] Simplify `examples/example.py`
- [ ] Port `examples/mcp_mud_demo.py`
- [ ] Update `prompts/system.md` (add auto-connection note)
- [ ] Update `README.md` (explain MCP architecture)
- [ ] Update `pyproject.toml` (version 0.10.0)

### Validation & Finalization
- [ ] Test example.py successfully
- [ ] Test mcp_mud_demo.py in both modes
- [ ] Test REPL with various configurations
- [ ] Test collision detection
- [ ] Test required vs optional server handling
- [ ] Verify Python 3.8 compatibility
- [ ] Run full test suite
- [ ] Document any behavior differences

---

## Known Differences & Gotchas

### 1. Subprocess Management

**Ruby:**
- Uses `Open3.popen3` which returns separate stdin/stdout/stderr/wait objects
- Automatic buffering behavior

**Python:**
- Uses `subprocess.Popen` with pipes
- Need to wrap with `io.TextIOWrapper` for line-buffered text I/O
- Must use `text=False` (binary mode) then wrap for proper buffering

```python
# Correct approach for line-delimited JSON:
proc = subprocess.Popen(
    cmd,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=env,
    text=False  # Binary mode
)

# Wrap for text I/O with line buffering
import io
self.stdin = io.TextIOWrapper(proc.stdin, encoding='utf-8', line_buffering=True)
self.stdout = io.TextIOWrapper(proc.stdout, encoding='utf-8', line_buffering=True)
```

### 2. JSON-RPC Protocol

**Key Points:**
- Protocol version must be exactly `"2025-06-18"`
- Requests need `id` field (can be any unique value)
- Notifications have no `id` field and expect no response
- Must read until specific response is found (may get other messages first)

**Handshake Sequence:**
1. Send `initialize` request → wait for response with same `id`
2. Send `notifications/initialized` notification → no response expected
3. Ready to call tools

### 3. Content Block Extraction

**Ruby:**
```ruby
content = result.dig("content")
return "" unless content.is_a?(Array)
text_block = content.find { |b| b["type"] == "text" }
text_block&.dig("text") || ""
```

**Python:**
```python
content = result.get("content", [])
if not isinstance(content, list):
    return ""
for block in content:
    if block.get("type") == "text":
        return block.get("text", "")
return ""
```

### 4. Tool Name Prefixing

**Critical:** Prefix is applied **client-side only**. The MCP server never sees it.

When calling a tool:
- Boukensha registry knows: `"tbamud__look"`
- Call to server uses: `"look"`

This allows multiple servers to provide same tool name without collision.

### 5. Collision Detection

**Always fatal**, even for optional servers. This is intentional:
- Collision means configuration error
- `required: false` means "ok if server doesn't start"
- Doesn't mean "ok to have naming conflicts"

### 6. Error Handling Hierarchy

1. **Subprocess spawn failure:**
   - Required server → Fatal error, exit
   - Optional server → Warn, continue

2. **CollisionError:**
   - Always fatal (even for optional servers)

3. **Tool execution error:**
   - Returned as data: `{"text": "error message", "error": True}`
   - Not raised as exception

### 7. Schema Conversion

**Enum handling:** MCP puts enum in separate field, Boukensha includes in description:

```python
# MCP format:
{
    "type": "string",
    "description": "Which direction",
    "enum": ["north", "south", "east", "west"]
}

# Boukensha format:
{
    "type": "string",
    "description": "Which direction (one of: north, south, east, west)"
}
```

### 8. Cleanup Hooks

**Ruby:** `at_exit` runs when Ruby exits

**Python:** `atexit.register` runs when Python exits

Both ensure MCP servers are cleaned up even if Boukensha crashes.

### 9. Environment Inheritance

MCP servers inherit boukensha's environment **plus** custom `env:` from config.

This means:
- Shell environment variables (like `MUD_HOST`) work without config
- Config `env:` overrides shell environment
- Useful for both development and production

### 10. Testing with mud-manager

Tests expect `mud-manager` to be installed and working:
```bash
# Test that it works:
mud-manager --mcp
# Should start MCP server and wait for JSON-RPC
```

If tests fail, check:
1. Is `mud-manager` in PATH?
2. Does it support `--mcp` flag?
3. Does it return 26+ tools?

---

## Technical Considerations

### MCP Protocol Version
- Current: `"2025-06-18"`
- Must match exactly or handshake fails
- Future: May need version negotiation

### Performance
- Each MCP server is a subprocess (resource cost)
- Servers started eagerly (all at boot)
- Consider lazy loading in future if needed

### Security
- Subprocess spawning uses shell=False (safe)
- Command and args come from config (trusted)
- Environment variables properly escaped
- No arbitrary code execution

### Limitations
1. **Line-delimited JSON only** - No streaming support
2. **Text content only** - Non-text blocks ignored
3. **Eager server spawning** - All servers start at boot
4. **No server recovery** - If server crashes, tools stop working

### Future Enhancements
- Lazy server spawning (on first tool use)
- Server health monitoring and restart
- Support for streaming responses
- Support for non-text content (images, etc.)
- Protocol version negotiation

---

## Success Criteria

### Must Have (P0)
- ✅ MCP client can spawn servers and complete handshake
- ✅ MCP client can discover tools via tools/list
- ✅ MCP client can call tools and get responses
- ✅ MCP tools integration registers all discovered tools
- ✅ Prefix mechanism prevents name collisions
- ✅ Config parses mcp_servers block correctly
- ✅ Main module registers servers before starting agent
- ✅ REPL shows server status in banner
- ✅ Required vs optional server handling works correctly
- ✅ Collision detection is always fatal

### Should Have (P1)
- ✅ Comprehensive test suite covering all functionality
- ✅ Tests use real mud-manager for integration testing
- ✅ All tests pass on Python 3.8+
- ✅ Error messages are clear and actionable

### Nice to Have (P2)
- ✅ Examples demonstrate both manual and config-based usage
- ✅ Documentation explains MCP architecture clearly
- ✅ README shows common configuration patterns
- ✅ Performance is reasonable (< 1s server startup)

---

## Estimated Total Effort

| Phase | Priority | Estimated Time |
|-------|----------|----------------|
| Phase 1: MCP Client | P0 | 3-4 hours |
| Phase 2: MCP Tools | P0 | 2-3 hours |
| Phase 3: Config | P0 | 1-2 hours |
| Phase 4: Main Module | P0 | 2 hours |
| Phase 5: REPL | P0 | 1 hour |
| Phase 6: Loader | P0 | 30 minutes |
| Phase 7: Tests | P1 | 4-5 hours |
| Phase 8: Examples/Docs | P2 | 1-2 hours |

**Total: 15-20 hours** (approximately 2-3 full work days)

---

## Dependencies on Previous Steps

Step 10 builds on step 09:
- ✅ Step 09 must be fully ported (global executable, loader pattern)
- ✅ Registry must support tool_names() method for collision detection
- ✅ Context, Message, Client, Agent all needed
- ✅ All backends must work (for LLM integration)
- ✅ REPL must support parameter extensions

**Note:** Step 10 is purely additive on top of step 09. No breaking changes to existing code.
