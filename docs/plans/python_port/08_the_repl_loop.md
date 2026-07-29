# Python Port Plan: Boukensha REPL Loop

## Overview
This plan outlines the port of the Boukensha REPL (Read-Eval-Print Loop) from Ruby to Python. Step 08 introduces an interactive session mode where users can have multi-turn conversations with the agent. Unlike `Boukensha.run()` which handles a single task and exits, `Boukensha.repl()` starts an interactive prompt that loops indefinitely until the user types `/exit` or presses Ctrl-D.

This is the final interactive layer - the "conversational" API that makes Boukensha feel like a chat interface.

## Scope
Port **Boukensha.repl** only:
- **Source:** `week1_baseline/ruby/08_the_repl_loop/`
- **Target:** `week1_baseline/python/08_the_repl_loop/`

**Key Changes from Step 07:**
- NEW: `lib/boukensha/repl.rb` → `boukensha/repl.py` (138 lines) - Interactive REPL class
- MODIFIED: `lib/boukensha.rb` → `boukensha/__init__.py` (adds `repl()` function, ~78 new lines)
- MODIFIED: `lib/boukensha/context.rb` → `boukensha/context.py` (adds `clear_messages!()` method)
- MODIFIED: `lib/boukensha/agent.rb` → `boukensha/agent.py` (persists final response in context)
- MODIFIED: `lib/boukensha/logger.rb` → `boukensha/logger.py` (adds `turn()` method)
- MODIFIED: `examples/example.rb` → `examples/example.py` (uses REPL instead of run)
- MODIFIED: `lib/boukensha/version.rb` → `boukensha/__init__.py` (VERSION = "0.8.0")
- UNCHANGED: All other files (copy from 07_the_run_dsl)

## Target Directory Structure

```
week1_baseline/
  ruby/08_the_repl_loop/     # Ruby (keep as reference)
  python/
    08_the_repl_loop/        # NEW: Python port
      boukensha/
        __init__.py          # MODIFIED: adds repl() function + VERSION
        repl.py              # NEW: Repl class
        agent.py             # MODIFIED: persist final response
        context.py           # MODIFIED: add clear_messages()
        logger.py            # MODIFIED: add turn() method
        client.py            # COPY from 07
        config.py            # COPY from 07
        errors.py            # COPY from 07
        message.py           # COPY from 07
        prompt_builder.py    # COPY from 07
        registry.py          # COPY from 07
        run_dsl.py           # COPY from 07
        tool.py              # COPY from 07
        backends/
          __init__.py        # COPY from 07
          base.py            # COPY from 07
          anthropic.py       # COPY from 07
          gemini.py          # COPY from 07
          ollama.py          # COPY from 07
          ollama_cloud.py    # COPY from 07
          openai.py          # COPY from 07
        tasks/
          __init__.py        # COPY from 07
          base.py            # COPY from 07
          player.py          # COPY from 07
      prompts/
        system.md            # COPY from 07
      examples/
        example.py           # MODIFIED: uses Boukensha.repl()
      requirements.txt       # COPY from 07
      README.md              # UPDATE for step 08
```

---

## File-by-File Mapping

| Ruby File | Python File | Lines | Complexity | Status | Notes |
|-----------|-------------|-------|------------|--------|-------|
| `lib/boukensha/repl.rb` | `boukensha/repl.py` | 138 | Medium | **NEW** | Interactive REPL loop |
| `lib/boukensha.rb` | `boukensha/__init__.py` | +78 | Medium | **MODIFIED** | Add `repl()` function |
| `lib/boukensha/agent.rb` | `boukensha/agent.py` | 159 (+3) | Low | **MODIFIED** | Add context persistence |
| `lib/boukensha/context.rb` | `boukensha/context.py` | 36 (+6) | Low | **MODIFIED** | Add clear_messages!() |
| `lib/boukensha/logger.rb` | `boukensha/logger.py` | 153 (no change) | Low | **MODIFIED** | Add turn() method (already exists!) |
| `examples/example.rb` | `examples/example.py` | 28 | Simple | **MODIFIED** | Use REPL |
| All other files | All other files | ~1400 | - | COPY | From 07_the_run_dsl |

**Total New/Modified Lines to Port:** ~225 lines (repl.py: 138, __init__.py: 78, agent.py: 3, context.py: 6, example.py: ~20)

**Key Translation Challenges:**
- Ruby `$stdin.gets` → Python `input()` or `sys.stdin.readline()`
- Ruby `$stdout.flush` → Python `sys.stdout.flush()`
- Ruby signal handling (`rescue Interrupt`) → Python `KeyboardInterrupt` exception
- Ruby EOF detection (`input.nil?`) → Python empty string from `input()` with try/except EOFError
- Ruby case/when for command parsing → Python dict mapping or if/elif
- Ruby string interpolation in banner → Python f-strings
- Ruby heredoc for banner → Python triple-quoted strings

---

## Dependencies

**External:**
- `python-dotenv` - .env file loading
- `requests` - HTTP client for API calls
- `PyYAML` - YAML parsing

**Stdlib:**
- `pathlib` - Path manipulation
- `os` - Environment variables
- `sys` - stdin/stdout access, exit handling
- `typing` - Type hints
- `abc` - Abstract base classes
- `json` - JSON parsing
- `datetime` - Timestamps
- `signal` - Signal handling (optional, for Ctrl-C)

---

## Key Translation Patterns

### 1. Ruby STDIN/STDOUT → Python sys.stdin/sys.stdout

Ruby has global variables for stdio:

```ruby
# Ruby
print PROMPT
$stdout.flush

input = $stdin.gets
break unless input  # EOF / Ctrl-D

input = input.chomp.strip
```

Python uses sys module:

```python
# Python
import sys

print(PROMPT, end='', flush=True)

try:
    input_line = input()  # Built-in, handles flushing
except EOFError:
    break  # Ctrl-D pressed

input_line = input_line.strip()
```

**Alternative (more explicit):**

```python
# Python - explicit readline
import sys

sys.stdout.write(PROMPT)
sys.stdout.flush()

input_line = sys.stdin.readline()
if not input_line:  # EOF
    break

input_line = input_line.strip()
```

### 2. Ruby Interrupt Handling → Python KeyboardInterrupt

```ruby
# Ruby - module-level rescue
def self.repl(...)
  # ... repl logic ...
rescue Interrupt
  puts "\nInterrupted."
ensure
  logger&.close
end
```

```python
# Python - try/except at function level
def repl(...):
    try:
        # ... repl logic ...
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        if logger:
            logger.close()
```

### 3. Ruby Heredoc Banner → Python Triple-Quoted Strings

```ruby
# Ruby
BANNER = <<~BANNER
  ╔══════════════════════════════════════╗
  ║  BOUKENSHA MUD Assistant (v#{ver})#{" " * (9 - ver.length)}║
  ╚══════════════════════════════════════╝
    config:    #{config_line}
BANNER
```

```python
# Python
def banner(self) -> str:
    ver = self._version or "?.?.?"
    padding = " " * (9 - len(ver))
    
    return f"""
╔══════════════════════════════════════╗
║  BOUKENSHA MUD Assistant (v{ver}){padding}║
╚══════════════════════════════════════╝
  config:    {config_line}
"""
```

### 4. Ruby Case/When → Python Dict or If/Elif

```ruby
# Ruby
case input
when "/exit", "/quit"
  puts "Goodbye."
  break
when "/help"
  puts HELP
  next
when "/quiet"
  Boukensha.quiet!
  puts "(logging suppressed)"
  next
end
```

```python
# Python - if/elif approach (clearest for commands)
if input_line in ("/exit", "/quit"):
    print("Goodbye.")
    break
elif input_line == "/help":
    print(HELP)
    continue
elif input_line == "/quiet":
    boukensha.quiet()
    print("(logging suppressed)")
    continue
```

**Alternative (dict-based, more scalable):**

```python
# Python - dict dispatch
def handle_exit():
    print("Goodbye.")
    return "exit"

def handle_help():
    print(HELP)
    return "continue"

commands = {
    "/exit": handle_exit,
    "/quit": handle_exit,
    "/help": handle_help,
    # ...
}

if input_line in commands:
    result = commands[input_line]()
    if result == "exit":
        break
    elif result == "continue":
        continue
```

### 5. Ruby Loop Control (next/break) → Python continue/break

Ruby's `next` is Python's `continue`:

```ruby
# Ruby
loop do
  input = gets
  next if input.empty?  # Skip to next iteration
  break if input == "exit"  # Exit loop
end
```

```python
# Python
while True:
    input_line = input()
    if not input_line:
        continue  # Skip to next iteration
    if input_line == "exit":
        break  # Exit loop
```

### 6. Ruby Safe Navigation (&.) → Python Optional Chaining (if/and)

```ruby
# Ruby
logger&.close
```

```python
# Python
if logger:
    logger.close()
```

### 7. Context Persistence - Agent.run() Modification

The key behavioral change in step 08:

```ruby
# Step 07 (07_the_run_dsl) - final response NOT added to context
def run
  loop do
    # ...
    if parsed[:stop_reason] == "tool_use"
      handle_tool_calls(...)
    else
      text = extract_text(...)
      log_response(...)
      return text  # ← NOT added to @context.messages
    end
  end
end
```

```ruby
# Step 08 (08_the_repl_loop) - final response ADDED to context
def run
  loop do
    # ...
    if parsed[:stop_reason] == "tool_use"
      handle_tool_calls(...)
    else
      text = extract_text(...)
      log_response(...)
      @context.add_message(:assistant, text)  # ← NEW: persist in context
      return text
    end
  end
end
```

This change means:
- In step 07: each `Boukensha.run()` call is isolated, context is discarded
- In step 08: REPL maintains conversation history across turns

The same change applies to the `wrap_up()` method (3 places total).

---

## Implementation Phases

### Phase 1: Copy from 07_the_run_dsl

**Priority:** HIGH  
**Estimated Time:** 15 minutes

Since Step 08 only adds new functionality without modifying most existing files, start by copying the entire 07_the_run_dsl directory:

```bash
cp -r week1_baseline/python/07_the_run_dsl week1_baseline/python/08_the_repl_loop
```

**Validation:**
- Directory structure matches 07_the_run_dsl
- All files present

---

### Phase 2: Modify Agent - Persist Final Response

**Priority:** HIGH  
**Estimated Time:** 15 minutes

**File:** `boukensha/agent.py` (MODIFIED)

**Changes:** Add `@context.add_message(:assistant, text)` before returning in 3 places:
1. Line 52: Main loop completion path
2. Line 94: Wrap-up success path
3. Line 99: Wrap-up fallback path

**Ruby Reference:** `week1_baseline/ruby/08_the_repl_loop/lib/boukensha/agent.rb` (lines 52, 94, 99)

**Python Changes:**

```python
# In run() method - main completion path (around line 130)
else:
    text = self._extract_text(parsed["content"])
    self._log_response(text=text, response=response)
    self._logger.turn_end(reason="completed", iterations=self._iteration)
    self._context.add_message("assistant", text)  # ← ADD THIS LINE
    return text
```

```python
# In _wrap_up() method - success path (around line 176)
text = fallback_message(reason) if not text.strip() else text
self._log_response(text=text, response=response)
self._logger.turn_end(reason=reason, iterations=self._iteration)
self._context.add_message("assistant", text)  # ← ADD THIS LINE
return text
```

```python
# In _wrap_up() method - error fallback (around line 179)
except ApiError:
    msg = fallback_message(reason)
    self._logger.turn_end(reason=reason, iterations=self._iteration)
    self._context.add_message("assistant", msg)  # ← ADD THIS LINE
    return msg
```

**Validation:**
- Agent adds final response to context before returning
- Conversation history persists across turns

---

### Phase 3: Modify Context - Add clear_messages!()

**Priority:** HIGH  
**Estimated Time:** 10 minutes

**File:** `boukensha/context.py` (MODIFIED)

**Changes:** Add `clear_messages()` method to wipe message history while keeping tools

**Ruby Reference:**
```ruby
# Drop all conversation history, keeping tools and system prompt intact.
# Used by the REPL's `clear` command.
def clear_messages!
  @messages = []
end
```

**Python Implementation:**

```python
def clear_messages(self) -> None:
    """
    Drop all conversation history, keeping tools and system prompt intact.
    
    Used by the REPL's /clear command to reset the conversation while
    preserving registered tools.
    """
    self._messages = []
```

**Validation:**
- Messages are cleared
- Tools remain registered
- System prompt unchanged

---

### Phase 4: Modify Logger - Add turn() Method

**Priority:** HIGH  
**Estimated Time:** 10 minutes

**File:** `boukensha/logger.py` (MODIFIED)

**Note:** Check if `turn()` method already exists in Python 07. The Ruby version has it in step 08, but it's a simple logging method.

**Ruby Reference:**
```ruby
def turn(n:)
  write_log(phase: "turn", n: n)
end
```

**Python Implementation:**

```python
def turn(self, n: int) -> None:
    """Log REPL turn header."""
    self._write_log({"phase": "turn", "n": n})
```

**Validation:**
- Turn events logged correctly
- Shows up in JSONL session files

---

### Phase 5: Port Repl Class

**Priority:** HIGH  
**Estimated Time:** 2 hours

**File:** `boukensha/repl.py` (NEW)

**Steps:**
1. Create `boukensha/repl.py`
2. Port the `Repl` class with full type hints
3. Implement the interactive loop with proper signal handling
4. Add built-in commands (/help, /quiet, /loud, /clear, /exit, /quit)
5. Implement banner generation
6. Add error handling for LoopError and ApiError

**Ruby Reference:** `week1_baseline/ruby/08_the_repl_loop/lib/boukensha/repl.rb` (138 lines)

**Python Structure:**

```python
"""
Interactive REPL (Read-Eval-Print Loop) for Boukensha.

Provides a conversational interface where users can have multi-turn
conversations with the agent. Conversation history accumulates across
turns, and built-in commands allow control of the session.
"""

from __future__ import annotations
import sys
from typing import TYPE_CHECKING, Optional, Dict, Any

if TYPE_CHECKING:
    from boukensha.context import Context
    from boukensha.registry import Registry
    from boukensha.prompt_builder import PromptBuilder
    from boukensha.client import Client
    from boukensha.logger import Logger

from boukensha.agent import Agent
from boukensha.errors import LoopError, ApiError


class Repl:
    """
    Interactive session loop for Boukensha.
    
    Wraps the same primitives as Boukensha.run(), but instead of running
    once it stays alive: reads tasks from stdin, runs the agent, prints
    replies, and loops back to the prompt.
    
    The Context is shared across every turn so conversation history
    accumulates naturally - the agent sees the full transcript each time.
    
    Built-in commands (not sent to the agent):
        /help    print the command list
        /quiet   suppress detailed logging
        /loud    re-enable logging
        /clear   wipe conversation history (tools stay registered)
        /exit    leave the REPL
        /quit    alias for /exit
    """
    
    PROMPT = "boukensha> "
    
    HELP = """Commands:
  /quiet   suppress logging output
  /loud    re-enable logging output
  /clear   wipe conversation history (tools stay)
  /exit    leave the REPL
  /help    show this message
"""
    
    def __init__(
        self,
        context: Context,
        registry: Registry,
        builder: PromptBuilder,
        client: Client,
        logger: Logger,
        task_settings: Optional[Dict[str, Any]] = None,
        max_iterations: Optional[int] = None,
        max_output_tokens: Optional[int] = None,
        config_dir: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        version: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> None:
        """Initialize REPL with agent components."""
        self._context = context
        self._registry = registry
        self._builder = builder
        self._client = client
        self._logger = logger
        self._task_settings = task_settings
        self._max_iterations = max_iterations
        self._max_output_tokens = max_output_tokens
        self._config_dir = config_dir
        self._provider = provider
        self._model = model
        self._version = version
        self._api_key = api_key
        self._turn = 0
    
    def start(self) -> None:
        """Start the interactive REPL loop."""
        print(self._banner())
        
        while True:
            try:
                # Prompt for input
                print(self.PROMPT, end='', flush=True)
                
                try:
                    input_line = input()
                except EOFError:
                    # Ctrl-D pressed
                    break
                
                input_line = input_line.strip()
                if not input_line:
                    continue
                
                # Handle built-in commands
                if input_line in ("/exit", "/quit"):
                    print("Goodbye.")
                    break
                elif input_line == "/help":
                    print(self.HELP)
                    continue
                elif input_line == "/quiet":
                    import boukensha
                    boukensha.quiet()
                    print("(logging suppressed — type /loud to re-enable)")
                    continue
                elif input_line == "/loud":
                    import boukensha
                    boukensha.loud()
                    print("(logging enabled)")
                    continue
                elif input_line == "/clear":
                    self._context.clear_messages()
                    self._turn = 0
                    print("(conversation history cleared)")
                    continue
                
                # Run agent turn
                self._run_turn(input_line)
                
            except KeyboardInterrupt:
                # Ctrl-C pressed
                print("\nInterrupted.")
                break
    
    def _banner(self) -> str:
        """Generate startup banner."""
        # API key status
        key_status = "✗ API key not set" if not self._api_key or not self._api_key.strip() else "✓ API key set"
        
        # Provider line
        provider_str = self._provider or "default"
        model_str = self._model or "default"
        provider_line = f"{provider_str} ({model_str})  {key_status}"
        
        # Config directory line
        import os
        config_exists = self._config_dir and os.path.isdir(self._config_dir)
        if config_exists:
            config_line = self._config_dir
        else:
            config_dir_str = self._config_dir or "(default)"
            config_line = f"{config_dir_str}  ✗ directory not found"
        
        # Version
        ver = self._version or "?.?.?"
        padding = " " * (9 - len(ver))
        
        return f"""
╔══════════════════════════════════════╗
║  BOUKENSHA MUD Assistant (v{ver}){padding}║
╚══════════════════════════════════════╝
  config:    {config_line}
  provider:  {provider_line}

  /quiet or /loud   toggle logging
  /clear           reset conversation history
  /exit or /quit    leave the REPL

"""
    
    def _run_turn(self, input_text: str) -> None:
        """Execute one turn of the conversation."""
        self._turn += 1
        self._logger.turn(n=self._turn)
        
        self._context.add_message("user", input_text)
        
        try:
            agent = Agent(
                context=self._context,
                registry=self._registry,
                builder=self._builder,
                client=self._client,
                logger=self._logger,
                task_settings=self._task_settings,
                max_iterations=self._max_iterations,
                max_output_tokens=self._max_output_tokens
            )
            result = agent.run()
            
            # Print the final response outside of the logger so it is always
            # visible, even when quiet mode is active.
            print()
            print(result)
            
        except LoopError as e:
            print(f"\n[error] {e}")
        except ApiError as e:
            print(f"\n[error] API call failed: {e}")
```

**Validation:**
- REPL starts and shows banner
- Prompt appears and accepts input
- Built-in commands work (/help, /quiet, /loud, /clear, /exit)
- Ctrl-D exits gracefully
- Ctrl-C exits gracefully
- Conversation history persists across turns
- Agent responses are always visible (even in quiet mode)

---

### Phase 6: Add repl() Function to __init__.py

**Priority:** HIGH  
**Estimated Time:** 1 hour

**File:** `boukensha/__init__.py` (MODIFIED)

**Steps:**
1. Import `Repl` from `.repl`
2. Add `VERSION = "0.8.0"` constant
3. Add the `repl()` function with full type hints
4. Implement similar setup logic as `run()`, minus the `task` parameter
5. Create `Repl` instance and call `.start()`
6. Handle `Interrupt` (KeyboardInterrupt) exception
7. Ensure logger closes in finally block

**Ruby Reference:** Lines 102-170 of `week1_baseline/ruby/08_the_repl_loop/lib/boukensha.rb`

**Python Implementation:**

```python
# At top of file
VERSION = "0.8.0"

# After run() function
def repl(
    *,
    system: Optional[str] = None,
    model: Optional[str] = None,
    backend: Optional[str] = None,
    api_key: Optional[str] = None,
    ollama_host: str = "http://localhost:11434",
    log: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
    block: Optional[Callable[[RunDSL], None]] = None
) -> None:
    """
    Interactive REPL: register tools once, then loop - reading tasks from
    stdin, running the agent, and printing replies - until the user types
    exit or sends EOF.
    
    Conversation history accumulates across every turn so the agent always
    sees the full transcript.
    
    Options are the same as Boukensha.run, minus `task` (the user supplies
    tasks interactively). system/model/backend/api_key all default to
    config values.
    
    Args:
        system: System prompt (defaults to task's system prompt)
        model: Model name (defaults to task's model setting)
        backend: "anthropic", "openai", "gemini", "ollama", or "ollama_cloud"
        api_key: API key for the backend (defaults to env var)
        ollama_host: Ollama base URL (default: http://localhost:11434)
        log: Optional JSONL log path (defaults to .boukensha/sessions/<id>.jsonl)
        max_output_tokens: Max tokens per response (defaults to task setting)
        block: Optional callable for tool registration: block(dsl: RunDSL) -> None
    
    Example:
        def my_tools(dsl):
            dsl.tool("read_file",
                     description="Read a file",
                     parameters={"path": {"type": "string"}},
                     implementation=lambda path: open(path).read())
        
        boukensha.repl(block=my_tools)
    """
    from .repl import Repl
    
    logger = None
    try:
        # Setup (same as run(), minus the user message)
        cfg = config()
        task_class = Player
        task_settings = cfg.tasks(task_class.task_name())
        
        if system is None:
            system = task_class.system_prompt(
                task_settings,
                user_prompts_dir=cfg.user_prompts_dir,
                default_prompts_dir=Config.PROMPTS_DIR
            )
        
        if model is None:
            model = task_class.model(task_settings)
        
        if backend is None:
            backend = task_class.provider(task_settings)
        
        if api_key is None:
            api_key_map = {
                "anthropic": "ANTHROPIC_API_KEY",
                "openai": "OPENAI_API_KEY",
                "gemini": "GEMINI_API_KEY",
                "ollama_cloud": "OLLAMA_API_KEY",
            }
            env_var = api_key_map.get(backend)
            if env_var:
                api_key = os.getenv(env_var)
        
        # Create components
        ctx = Context(task=task_class, system=system)
        registry = Registry(ctx)
        
        # Execute tool registration block
        if block:
            dsl = RunDSL(registry)
            block(dsl)
        
        # Backend selection
        backend_factories = {
            "anthropic": lambda: backends.Anthropic(api_key=api_key, model=model),
            "openai": lambda: backends.OpenAI(api_key=api_key, model=model),
            "gemini": lambda: backends.Gemini(api_key=api_key, model=model),
            "ollama": lambda: backends.Ollama(host=ollama_host, model=model),
            "ollama_cloud": lambda: backends.OllamaCloud(api_key=api_key, model=model),
        }
        
        if backend not in backend_factories:
            raise ValueError(
                f"Unknown backend {backend!r}. "
                f"Use 'anthropic', 'openai', 'gemini', 'ollama', or 'ollama_cloud'."
            )
        
        be = backend_factories[backend]()
        
        builder = PromptBuilder(ctx, be)
        client = Client(builder)
        effective_max_iterations = task_class.max_iterations(task_settings)
        effective_max_output_tokens = max_output_tokens or task_class.max_output_tokens(task_settings)
        
        logger = Logger(
            log=log,
            snapshot={
                "task": task_class.task_name(),
                "max_iterations": effective_max_iterations,
                "max_output_tokens": effective_max_output_tokens,
                "model": model,
                "provider": backend
            }
        )
        
        # Create and start REPL
        repl_instance = Repl(
            context=ctx,
            registry=registry,
            builder=builder,
            client=client,
            logger=logger,
            task_settings=task_settings,
            max_iterations=effective_max_iterations,
            max_output_tokens=effective_max_output_tokens,
            config_dir=cfg.dir,
            provider=backend,
            model=model,
            version=VERSION,
            api_key=api_key
        )
        repl_instance.start()
        
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        if logger:
            logger.close()
```

**Validation:**
- Function signature correct
- All components wire together
- REPL starts successfully
- Logger closes on exit

---

### Phase 7: Port Example

**Priority:** HIGH  
**Estimated Time:** 20 minutes

**File:** `examples/example.py` (MODIFIED)

**Steps:**
1. Update to use `boukensha.repl()` instead of `boukensha.run()`
2. Remove the task argument
3. Keep the same tools (read_file, list_directory)

**Ruby Reference:** `examples/example.rb` (28 lines)

**Python Implementation:**

```python
import os
import sys
from pathlib import Path

# Set BOUKENSHA_DIR to point to .boukensha in repo root
if "BOUKENSHA_DIR" not in os.environ:
    os.environ["BOUKENSHA_DIR"] = str(
        Path(__file__).parent.parent.parent.parent / ".boukensha"
    )

# Add parent to path so we can import boukensha
sys.path.insert(0, str(Path(__file__).parent.parent))

import boukensha

# Config is loaded automatically inside boukensha.repl() — system prompt, model,
# and API key all come from .boukensha (or BOUKENSHA_DIR) by default.

print(f"Config: {boukensha.config()}")
print()

# The base directory tools will operate relative to — step 07 folder makes
# a good playground since it has source files to read.
base_dir = Path(__file__).parent.parent.parent / "07_the_run_dsl"

def register_tools(dsl):
    """Register tools for the agent."""
    
    def read_file_impl(path: str) -> str:
        """Read the contents of a file from disk."""
        full_path = base_dir / path
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
        full_path = base_dir / path
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
                "description": "Directory path (relative to the working directory, or '.' for root)"
            }
        },
        implementation=list_directory_impl
    )

# Start the REPL
boukensha.repl(block=register_tools)
```

**Validation:**
- Example runs without errors
- REPL starts and shows prompt
- Tools are registered correctly
- User can interact with agent
- Multi-turn conversations work
- /clear command resets history but keeps tools
- /exit command exits cleanly

---

### Phase 8: Update VERSION

**Priority:** LOW  
**Estimated Time:** 5 minutes

**File:** `boukensha/__init__.py` (MODIFIED)

Add version constant at top of file:

```python
# Near the top of boukensha/__init__.py
VERSION = "0.8.0"
```

**Validation:**
- Version shows in REPL banner

---

## Testing Strategy

### Manual Validation

1. **Run the REPL example:**
   ```bash
   cd week1_baseline/python/08_the_repl_loop
   python examples/example.py
   ```

2. **Test REPL commands:**
   ```
   boukensha> /help
   # Should show help text
   
   boukensha> list the files in the lib directory
   # Agent should call list_directory tool
   
   boukensha> read lib/boukensha/agent.py
   # Agent should call read_file tool
   
   boukensha> what was the first thing I asked you?
   # Agent should remember (conversation history)
   
   boukensha> /clear
   # History cleared
   
   boukensha> what did I just ask you?
   # Agent should not remember (history cleared)
   
   boukensha> /quiet
   # Logging suppressed
   
   boukensha> /loud
   # Logging re-enabled
   
   boukensha> /exit
   # Should exit cleanly
   ```

3. **Test signal handling:**
   - Press Ctrl-D → should exit with no error
   - Press Ctrl-C → should print "Interrupted." and exit

4. **Verify session logging:**
   - Check `.boukensha/sessions/<id>.jsonl` exists
   - Verify turn events are logged
   - Verify all turns are in single session file

5. **Compare with Ruby:**
   ```bash
   # Run Ruby version
   week1_baseline/bin/ruby/08_the_repl_loop
   
   # Compare behavior and output
   ```

### Unit Tests (Optional - Future)

- Test `Repl._banner()` generates correct banner
- Test `Repl._run_turn()` handles errors correctly
- Test Context.clear_messages() preserves tools
- Test Agent persists final response to context

---

## Migration Checklist

### Pre-Port
- [x] Analyze Ruby codebase structure
- [x] Identify changes from Step 07
- [x] Document translation patterns
- [x] Create porting plan

### Step 08 Port
- [ ] Copy entire `07_the_run_dsl` directory to `08_the_repl_loop`
- [ ] Modify `boukensha/agent.py` - add context persistence (3 lines)
- [ ] Modify `boukensha/context.py` - add clear_messages() method
- [ ] Check `boukensha/logger.py` - verify turn() method exists (or add it)
- [ ] Create `boukensha/repl.py` with `Repl` class
- [ ] Add `repl()` function to `boukensha/__init__.py`
- [ ] Add `VERSION = "0.8.0"` to `boukensha/__init__.py`
- [ ] Update `examples/example.py` to use REPL
- [ ] Update `README.md` to document Step 08

### Testing & Finalization
- [ ] Run `examples/example.py` successfully
- [ ] Test all REPL commands (/help, /quiet, /loud, /clear, /exit)
- [ ] Test Ctrl-D and Ctrl-C handling
- [ ] Verify conversation history persists across turns
- [ ] Verify /clear resets history but keeps tools
- [ ] Verify session logging works
- [ ] Compare output with Ruby version
- [ ] Add type checking with mypy (optional)
- [ ] Document any behavior differences

---

## Known Differences & Gotchas

### 1. **STDIN/STDOUT Access**

**Ruby:** Uses global variables `$stdin`, `$stdout`  
**Python:** Uses `sys.stdin`, `sys.stdout` or built-in `input()`

The built-in `input()` function is simpler and handles flushing automatically, making it preferable for interactive prompts.

### 2. **EOF Handling**

**Ruby:** `gets` returns `nil` on EOF  
**Python:** `input()` raises `EOFError` on EOF

Must wrap `input()` in try/except to handle Ctrl-D gracefully.

### 3. **Interrupt Signal**

**Ruby:** `rescue Interrupt` at module level  
**Python:** `except KeyboardInterrupt` in try/except block

Both handle Ctrl-C, but Python requires explicit exception handling.

### 4. **Loop Control**

**Ruby:** `next` skips to next iteration, `break` exits loop  
**Python:** `continue` skips to next iteration, `break` exits loop

Direct translation, just different keywords.

### 5. **String Formatting in Banner**

**Ruby:** Heredoc with interpolation `<<~BANNER ... #{var} ... BANNER`  
**Python:** f-string with triple quotes `f"""... {var} ..."""`

Both support multi-line strings with variable interpolation, just different syntax.

### 6. **Context Persistence**

This is a **behavioral change** from step 07 to step 08, not a Ruby vs Python difference:

- **Step 07:** Agent.run() returns final response WITHOUT adding it to context
- **Step 08:** Agent.run() returns final response AFTER adding it to context

This enables conversation history to persist across REPL turns.

### 7. **Logger turn() Method**

The Ruby version adds `turn()` method in step 08, but the Python version may already have it from an earlier step. Check the Python 07 logger before adding.

### 8. **Module State for quiet/loud**

**Ruby:** `@quiet` module instance variable  
**Python:** `_quiet` module-level global (already implemented in step 07)

The `quiet()` and `loud()` functions should already exist from step 07.

---

## Success Criteria

All criteria must be met:

- [ ] `Repl` class implemented with proper type hints
- [ ] `repl()` function implemented in `__init__.py`
- [ ] Agent persists final response to context (3 places)
- [ ] Context has `clear_messages()` method
- [ ] Logger has `turn()` method
- [ ] All built-in commands work (/help, /quiet, /loud, /clear, /exit, /quit)
- [ ] Ctrl-D exits gracefully (EOF handling)
- [ ] Ctrl-C exits gracefully (KeyboardInterrupt handling)
- [ ] Conversation history persists across turns
- [ ] /clear resets history but preserves tools
- [ ] Agent responses always visible (even in quiet mode)
- [ ] Example runs successfully and enters REPL
- [ ] Session logging works (turn events in JSONL)
- [ ] Banner displays correctly with version, config, provider info
- [ ] Code is compatible with Python 3.8+
- [ ] Type hints are comprehensive
- [ ] Code follows Python best practices (PEP 8)
- [ ] No regressions from Step 07 functionality

---

## Timeline Estimate

| Phase | Estimated Time | Complexity |
|-------|----------------|------------|
| Copy from 07_the_run_dsl | 15 min | Trivial |
| Modify Agent (context persistence) | 15 min | Simple |
| Modify Context (clear_messages) | 10 min | Simple |
| Modify Logger (turn method) | 10 min | Simple |
| Port Repl class | 2 hours | Medium |
| Add repl() function to __init__ | 1 hour | Medium |
| Port example.py | 20 min | Simple |
| Update VERSION | 5 min | Trivial |
| Testing & validation | 1 hour | Medium |
| Documentation updates | 20 min | Low |
| **Total** | **5-6 hours** | - |

**Note:** Most time is spent on the `Repl` class and `repl()` function which handle interactive I/O, signal handling, and command parsing. The actual amount of new code is moderate (~225 lines), but it requires careful handling of edge cases (EOF, Ctrl-C, empty input, etc.).

---

## Ruby → Python REPL-Specific Patterns

### Input Loop Pattern

```ruby
# Ruby
loop do
  print PROMPT
  $stdout.flush
  
  input = $stdin.gets
  break unless input  # EOF
  
  input = input.chomp.strip
  next if input.empty?
  
  # ... process input
end
```

```python
# Python
while True:
    print(PROMPT, end='', flush=True)
    
    try:
        input_line = input()
    except EOFError:
        break
    
    input_line = input_line.strip()
    if not input_line:
        continue
    
    # ... process input
```

### Banner with Dynamic Content

```ruby
# Ruby
def banner
  ver = @version || "?.?.?"
  <<~BANNER
    ╔══════════════════════════════════════╗
    ║  BOUKENSHA MUD Assistant (v#{ver})#{" " * (9 - ver.length)}║
    ╚══════════════════════════════════════╝
  BANNER
end
```

```python
# Python
def _banner(self) -> str:
    ver = self._version or "?.?.?"
    padding = " " * (9 - len(ver))
    return f"""
╔══════════════════════════════════════╗
║  BOUKENSHA MUD Assistant (v{ver}){padding}║
╚══════════════════════════════════════╝
"""
```

### Safe Method Chaining

```ruby
# Ruby
logger&.close
```

```python
# Python
if logger:
    logger.close()
```

---

## Next Steps

**Ready to start!** Begin with:

```bash
# Copy entire 07_the_run_dsl directory
cp -r week1_baseline/python/07_the_run_dsl week1_baseline/python/08_the_repl_loop
cd week1_baseline/python/08_the_repl_loop
```

Then modify files in this order:

1. Modify `boukensha/agent.py` - add 3 lines for context persistence
2. Modify `boukensha/context.py` - add clear_messages() method (6 lines)
3. Check/modify `boukensha/logger.py` - verify turn() method exists
4. Create `boukensha/repl.py` - full Repl class (138 lines)
5. Modify `boukensha/__init__.py` - add VERSION + repl() function (78 new lines)
6. Modify `examples/example.py` - use repl() instead of run() (28 lines)
7. Update `README.md` to reflect Step 08
8. Test by running `python examples/example.py`

**Key files to reference:**
- `week1_baseline/ruby/08_the_repl_loop/lib/boukensha/repl.rb` (138 lines)
- `week1_baseline/ruby/08_the_repl_loop/lib/boukensha.rb` (lines 102-170 for `repl()` method)
- `week1_baseline/ruby/08_the_repl_loop/lib/boukensha/agent.rb` (lines 52, 94, 99 for context persistence)
- `week1_baseline/ruby/08_the_repl_loop/lib/boukensha/context.rb` (lines 23-27 for clear_messages!)
- `week1_baseline/ruby/08_the_repl_loop/examples/example.rb` (28 lines)
