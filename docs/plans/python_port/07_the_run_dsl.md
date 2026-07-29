# Python Port Plan: Boukensha.run DSL

## Overview
This plan outlines the port of the Boukensha.run DSL from Ruby to Python. Step 7 introduces a single top-level entry point `Boukensha.run()` that hides all the plumbing (Context, Registry, Backend, PromptBuilder, Client, Logger, Agent) behind one function call with a block/callable for tool registration.

This is the final convenience layer - the "hello world" API that makes Boukensha easy to use.

## Scope
Port **Boukensha.run DSL** only:
- **Source:** `week1_baseline/ruby/07_the_run_dsl/`
- **Target:** `week1_baseline/python/07_the_run_dsl/`

**Key Changes from Step 06:**
- NEW: `lib/boukensha/run_dsl.rb` → `boukensha/run_dsl.py` (13 lines)
- MODIFIED: `lib/boukensha.rb` → `boukensha/__init__.py` (adds `run()` function, ~60 new lines)
- MODIFIED: `examples/example.rb` → `examples/example.py` (uses new DSL)
- UNCHANGED: All other files (copy from 06_the_logger)

## Target Directory Structure

```
week1_baseline/
  ruby/07_the_run_dsl/     # Ruby (keep as reference)
  python/
    07_the_run_dsl/        # NEW: Python port
      boukensha/
        __init__.py        # MODIFIED: adds run() function
        run_dsl.py         # NEW: RunDSL class
        agent.py           # COPY from 06
        client.py          # COPY from 06
        config.py          # COPY from 06
        context.py         # COPY from 06
        errors.py          # COPY from 06
        logger.py          # COPY from 06
        message.py         # COPY from 06
        prompt_builder.py  # COPY from 06
        registry.py        # COPY from 06
        tool.py            # COPY from 06
        backends/
          __init__.py      # COPY from 06
          base.py          # COPY from 06
          anthropic.py     # COPY from 06
          gemini.py        # COPY from 06
          ollama.py        # COPY from 06
          ollama_cloud.py  # COPY from 06
          openai.py        # COPY from 06
        tasks/
          __init__.py      # COPY from 06
          base.py          # COPY from 06
          player.py        # COPY from 06
      prompts/
        system.md          # COPY from 06
      examples/
        example.py         # MODIFIED: uses Boukensha.run()
      requirements.txt     # COPY from 06
      README.md            # COPY from 06
```

---

## File-by-File Mapping

| Ruby File | Python File | Lines | Complexity | Status | Notes |
|-----------|-------------|-------|------------|--------|-------|
| `lib/boukensha/run_dsl.rb` | `boukensha/run_dsl.py` | 13 | Simple | **NEW** | DSL surface object |
| `lib/boukensha.rb` | `boukensha/__init__.py` | +60 | Medium | **MODIFIED** | Add `run()` function |
| `examples/example.rb` | `examples/example.py` | 36 | Simple | **MODIFIED** | Demonstrate DSL |
| `lib/boukensha/agent.rb` | `boukensha/agent.py` | 156 | - | COPY | From 06_the_logger |
| `lib/boukensha/client.rb` | `boukensha/client.py` | 78 | - | COPY | From 06_the_logger |
| `lib/boukensha/config.rb` | `boukensha/config.py` | 96 | - | COPY | From 06_the_logger |
| `lib/boukensha/context.rb` | `boukensha/context.py` | 29 | - | COPY | From 06_the_logger |
| `lib/boukensha/errors.rb` | `boukensha/errors.py` | 6 | - | COPY | From 06_the_logger |
| `lib/boukensha/logger.rb` | `boukensha/logger.py` | 153 | - | COPY | From 06_the_logger |
| `lib/boukensha/message.rb` | `boukensha/message.py` | 8 | - | COPY | From 06_the_logger |
| `lib/boukensha/prompt_builder.rb` | `boukensha/prompt_builder.py` | 34 | - | COPY | From 06_the_logger |
| `lib/boukensha/registry.rb` | `boukensha/registry.py` | 20 | - | COPY | From 06_the_logger |
| `lib/boukensha/tool.rb` | `boukensha/tool.py` | 7 | - | COPY | From 06_the_logger |
| `lib/boukensha/backends/*.rb` | `boukensha/backends/*.py` | ~600 | - | COPY | All 6 backend files from 06 |
| `lib/boukensha/tasks/*.rb` | `boukensha/tasks/*.py` | ~80 | - | COPY | Both task files from 06 |
| `prompts/system.md` | `prompts/system.md` | - | - | COPY | As-is |

**Total New/Modified Lines to Port:** ~109 lines (run_dsl.py: 13, __init__.py: 60, example.py: 36)

**Key Translation Challenges:**
- Ruby `instance_eval(&block)` → Python callable pattern (can't change `self` in Python)
- Ruby block parameter `&block` → Python `Callable[[RunDSL], None]`
- Ruby keyword arguments with `||=` defaults → Python default parameters with conditional assignment
- Ruby case/when for backend selection → Python dict mapping
- Ruby symbols (`:anthropic`) → Python strings (`"anthropic"`)
- Module-level `@config`, `@quiet`, `@debug` → Python module globals

---

## Dependencies

**External:**
- `python-dotenv` - .env file loading
- `requests` - HTTP client for API calls
- `PyYAML` - YAML parsing

**Stdlib:**
- `pathlib` - Path manipulation
- `os` - Environment variables
- `typing` - Type hints (Callable, Optional, Union, Dict, Any)
- `abc` - Abstract base classes
- `json` - JSON parsing
- `datetime` - Timestamps

---

## Key Translation Patterns

### 1. Ruby instance_eval(&block) → Python Callable Pattern

Ruby uses `instance_eval` to execute a block with a different `self`:

```ruby
# Ruby
RunDSL.new(registry).instance_eval(&block) if block
```

Python cannot change `self`, so we pass the DSL object as a parameter instead:

```python
# Python
from typing import Callable, Optional

def run(..., block: Optional[Callable[[RunDSL], None]] = None) -> str:
    if block:
        dsl = RunDSL(registry)
        block(dsl)  # Pass dsl as parameter to the callable
```

The caller's syntax changes slightly:

```ruby
# Ruby - block with implicit self
Boukensha.run(task: "...") do
  tool "read_file", description: "...", parameters: {...} do |path:|
    File.read(path)
  end
end
```

```python
# Python - lambda/function with explicit dsl parameter
def run_example():
    def register_tools(dsl):
        def read_file_impl(path: str) -> str:
            return open(path).read()

        dsl.tool("read_file",
                 description="...",
                 parameters={...},
                 implementation=read_file_impl)

    boukensha.run(task="...", block=register_tools)
```

### 2. Module-Level run() Function with Keyword Args

```ruby
# Ruby
def self.run(
  task:,
  system: nil,
  model: nil,
  backend: nil,
  api_key: nil,
  ollama_host: "http://localhost:11434",
  log: nil,
  max_output_tokens: nil,
  &block
)
  system ||= task_class.system_prompt(...)
  # ...
end
```

```python
# Python
from typing import Optional, Callable

def run(
    *,  # Force keyword-only arguments
    task: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    backend: Optional[str] = None,
    api_key: Optional[str] = None,
    ollama_host: str = "http://localhost:11434",
    log: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
    block: Optional[Callable[["RunDSL"], None]] = None
) -> str:
    if system is None:
        system = task_class.system_prompt(...)
    # ...
```

### 3. Backend Selection - Case/When → Dict Mapping

```ruby
# Ruby - case/when with symbols
backend ||= task_class.provider(task_settings).to_sym

be = case backend
     when :anthropic    then Backends::Anthropic.new(api_key: api_key, model: model)
     when :openai       then Backends::OpenAI.new(api_key: api_key, model: model)
     when :gemini       then Backends::Gemini.new(api_key: api_key, model: model)
     when :ollama       then Backends::Ollama.new(host: ollama_host, model: model)
     when :ollama_cloud then Backends::OllamaCloud.new(api_key: api_key, model: model)
     else raise ArgumentError, "Unknown backend #{backend.inspect}"
     end
```

```python
# Python - dict mapping with strings
from . import backends

if backend is None:
    backend = task_class.provider(task_settings)

# Factory functions for each backend
backend_factories = {
    "anthropic": lambda: backends.Anthropic(api_key=api_key, model=model),
    "openai": lambda: backends.OpenAI(api_key=api_key, model=model),
    "gemini": lambda: backends.Gemini(api_key=api_key, model=model),
    "ollama": lambda: backends.Ollama(host=ollama_host, model=model),
    "ollama_cloud": lambda: backends.OllamaCloud(api_key=api_key, model=model),
}

if backend not in backend_factories:
    raise ValueError(f"Unknown backend {backend!r}. Use 'anthropic', 'openai', 'gemini', 'ollama', or 'ollama_cloud'.")

be = backend_factories[backend]()
```

### 4. API Key Selection by Backend

```ruby
# Ruby - case/when with ENV access
api_key ||= case backend
            when :anthropic    then ENV["ANTHROPIC_API_KEY"]
            when :openai       then ENV["OPENAI_API_KEY"]
            when :gemini       then ENV["GEMINI_API_KEY"]
            when :ollama_cloud then ENV["OLLAMA_API_KEY"]
            end
```

```python
# Python - dict mapping
import os

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
```

### 5. Module State Management

```ruby
# Ruby - module instance variables
module Boukensha
  @quiet  = False
  @debug  = False
  @config = nil

  def self.config
    @config ||= Config.new
  end

  def self.quiet?
    @quiet
  end
end
```

```python
# Python - module-level globals (already established in 06)
# In boukensha/__init__.py

_quiet: bool = False
_debug: bool = False
_config: Optional[Config] = None

def config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config

def is_quiet() -> bool:
    return _quiet
```

---

## Implementation Phases

### Phase 1: Copy from 06_the_logger

**Priority:** HIGH
**Estimated Time:** 15 minutes

Since Step 07 only adds new functionality without modifying existing files (except `__init__.py` and `example.py`), start by copying the entire 06_the_logger directory:

```bash
cp -r week1_baseline/python/06_the_logger week1_baseline/python/07_the_run_dsl
```

**Validation:**
- Directory structure matches 06_the_logger
- All files present

---

### Phase 2: Port RunDSL Class

**Priority:** HIGH
**Estimated Time:** 20 minutes

**File:** `boukensha/run_dsl.py` (NEW)

**Steps:**
1. Create `boukensha/run_dsl.py`
2. Port the `RunDSL` class:
   - `__init__(self, registry)` - stores registry reference
   - `tool(self, name, description, parameters={}, implementation)` - delegates to registry
3. Add type hints
4. Update imports in `boukensha/__init__.py` to include `RunDSL`

**Ruby Reference:**
```ruby
module Boukensha
  class RunDSL
    def initialize(registry)
      @registry = registry
    end

    def tool(name, description:, parameters: {}, &block)
      @registry.tool(name, description: description, parameters: parameters, &block)
    end
  end
end
```

**Python Target:**
```python
from typing import Dict, Callable, Any

class RunDSL:
    """DSL surface object for Boukensha.run() blocks.

    Exposes only the tool() method to keep the DSL surface intentionally small.
    """

    def __init__(self, registry):
        """Initialize with a Registry instance."""
        self._registry = registry

    def tool(
        self,
        name: str,
        *,
        description: str,
        parameters: Dict[str, Any] = None,
        implementation: Callable[..., Any]
    ) -> None:
        """Register a tool with the agent.

        Args:
            name: Tool name (e.g., "read_file")
            description: What the tool does
            parameters: JSON schema for tool parameters
            implementation: Callable that executes the tool
        """
        if parameters is None:
            parameters = {}
        self._registry.tool(
            name,
            description=description,
            parameters=parameters,
            implementation=implementation
        )
```

**Validation:**
- Class instantiates correctly
- `tool()` method delegates to registry properly

---

### Phase 3: Add run() Function to __init__.py

**Priority:** HIGH
**Estimated Time:** 1.5 hours

**File:** `boukensha/__init__.py` (MODIFIED)

**Steps:**
1. Add imports for all required components (Agent, Client, Logger, etc.)
2. Import `RunDSL` from `.run_dsl`
3. Add the `run()` function with full type hints
4. Implement the function body:
   - Load config (triggers .env loading)
   - Get task class (Tasks.Player)
   - Load task settings
   - Set defaults for system, model, backend using task settings
   - Set default api_key based on backend
   - Create Context and Registry
   - Execute block with RunDSL if provided
   - Create backend instance based on backend parameter
   - Create PromptBuilder, Client, Logger
   - Create Agent with all components
   - Add user message and run agent
   - Return final response
   - Ensure logger closes in finally block

**Ruby Reference:** Lines 55-111 of `week1_baseline/ruby/07_the_run_dsl/lib/boukensha.rb`

**Python Target Structure:**
```python
from typing import Optional, Callable
from .config import Config
from .context import Context
from .registry import Registry
from .run_dsl import RunDSL
from . import backends
from .prompt_builder import PromptBuilder
from .client import Client
from .logger import Logger
from .agent import Agent
from .tasks import Player
import os

def run(
    *,
    task: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    backend: Optional[str] = None,
    api_key: Optional[str] = None,
    ollama_host: str = "http://localhost:11434",
    log: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
    block: Optional[Callable[[RunDSL], None]] = None
) -> str:
    """Top-level DSL entry point for Boukensha.

    Wires together all components so the caller only describes *what* to do.

    Args:
        task: The user message to give the agent (required)
        system: System prompt (defaults to task's system prompt)
        model: Model name (defaults to task's model setting)
        backend: "anthropic", "openai", "gemini", "ollama", or "ollama_cloud"
        api_key: API key for the backend (defaults to env var)
        ollama_host: Ollama base URL (default: http://localhost:11434)
        log: Optional JSONL log path (defaults to .boukensha/sessions/<id>.jsonl)
        max_output_tokens: Max tokens per response (defaults to task setting)
        block: Optional callable for tool registration: block(dsl: RunDSL) -> None

    Returns:
        The agent's final text response

    Example:
        def my_tools(dsl):
            dsl.tool("read_file",
                     description="Read a file",
                     parameters={"path": {"type": "string"}},
                     implementation=lambda path: open(path).read())

        result = boukensha.run(task="Read README.md", block=my_tools)
    """
    # Implementation details...
```

**Key Implementation Details:**
- Use `config()` to get module-level config (loads .env)
- Task class is always `Player` (hardcoded like Ruby)
- Backend selection via dict mapping (see pattern 3 above)
- API key selection via dict mapping (see pattern 4 above)
- Call `block(dsl)` instead of `instance_eval`
- Use try/finally to ensure logger closes
- Return agent's final response string

**Validation:**
- Function signature matches documentation
- All components wire together correctly
- Logger closes even on exceptions
- Returns agent response string

---

### Phase 4: Port Example

**Priority:** HIGH
**Estimated Time:** 30 minutes

**File:** `examples/example.py` (MODIFIED)

**Steps:**
1. Update `examples/example.py` to use the new `boukensha.run()` DSL
2. Set `BOUKENSHA_DIR` env var to point to `.boukensha`
3. Define tool registration function
4. Call `boukensha.run()` with task and block

**Ruby Reference:** `examples/example.rb`

**Python Target:**
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
        """Read a file from disk."""
        full_path = base_dir / path
        return full_path.read_text()

    dsl.tool(
        "read_file",
        description="Read the contents of a file from disk",
        parameters={"path": {"type": "string", "description": "The file path to read"}},
        implementation=read_file_impl
    )

    def list_directory_impl(path: str) -> str:
        """List files in a directory."""
        full_path = base_dir / path
        entries = [
            e.name for e in full_path.iterdir()
            if not e.name.startswith(".")
        ]
        return ", ".join(entries)

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
```

**Validation:**
- Example runs without errors
- Tools are registered correctly
- Agent responds with summary of README.md
- Logger creates session file in `.boukensha/sessions/`

---

## Testing Strategy

### Manual Validation

1. **Run the example:**
   ```bash
   cd week1_baseline/python/07_the_run_dsl
   python examples/example.py
   ```

2. **Verify output:**
   - Config loads from `.boukensha/`
   - Both tools (`read_file`, `list_directory`) are registered
   - Agent calls tools and generates response
   - Logger output appears on stdout
   - Session JSONL file created in `.boukensha/sessions/`

3. **Compare with Ruby:**
   ```bash
   # Run Ruby version
   week1_baseline/bin/ruby/07_the_run_dsl

   # Compare behavior and output
   ```

4. **Test edge cases:**
   - Override system prompt
   - Override model
   - Use different backend (if available)
   - Pass no tools (block=None)

### Unit Tests (Optional - Future)

- Test `RunDSL.tool()` delegates to registry
- Test `run()` with minimal arguments
- Test `run()` with all arguments
- Test backend selection logic
- Test API key selection logic

---

## Migration Checklist

### Pre-Port
- [x] Analyze Ruby codebase structure
- [x] Identify changes from Step 06
- [x] Document translation patterns
- [x] Create porting plan

### Step 07 Port
- [ ] Copy entire `06_the_logger` directory to `07_the_run_dsl`
- [ ] Create `boukensha/run_dsl.py` with `RunDSL` class
- [ ] Add imports to `boukensha/__init__.py`
- [ ] Add `run()` function to `boukensha/__init__.py`
- [ ] Update `examples/example.py` to use DSL
- [ ] Update `README.md` to document Step 07

### Testing & Finalization
- [ ] Run `examples/example.py` successfully
- [ ] Verify session logging works
- [ ] Compare output with Ruby version
- [ ] Test with different backends (if available)
- [ ] Add type checking with mypy (optional)
- [ ] Document any behavior differences

---

## Known Differences & Gotchas

### 1. **No instance_eval in Python**

**Ruby:** Uses `instance_eval(&block)` to execute block with `RunDSL` as `self`
**Python:** Cannot change `self`, so we pass `dsl` as explicit parameter to callable

**Impact:** Caller syntax differs slightly:
```ruby
# Ruby - implicit self
Boukensha.run(...) do
  tool "name", ... do |args|
    # ...
  end
end
```

```python
# Python - explicit dsl parameter
def my_tools(dsl):
    dsl.tool("name", ..., implementation=lambda args: ...)

boukensha.run(..., block=my_tools)
```

### 2. **Block vs Callable**

**Ruby:** Uses Ruby blocks (`&block`, `yield`)
**Python:** Uses callables (functions, lambdas)

Nested blocks in Ruby become nested functions in Python:
```ruby
# Ruby
tool "read", ... do |path:|
  File.read(path)
end
```

```python
# Python
def read_impl(path: str) -> str:
    return open(path).read()

dsl.tool("read", ..., implementation=read_impl)
```

### 3. **Keyword Arguments**

**Ruby:** Uses `key:` syntax, `||=` for defaults
**Python:** Uses `key: type = default`, `if x is None:` for conditional defaults

Both support keyword-only arguments, but syntax differs.

### 4. **Symbol vs String**

**Ruby:** Uses symbols for backend (`:anthropic`, `:ollama`)
**Python:** Uses strings (`"anthropic"`, `"ollama"`)

This is a consistent pattern throughout the Python port.

### 5. **Module State**

**Ruby:** Module instance variables (`@config`, `@quiet`)
**Python:** Module-level globals with `global` keyword

Both approaches work, but Python requires explicit `global` in functions that modify state.

### 6. **Error Messages**

Ruby's `ArgumentError` becomes Python's `ValueError` for invalid arguments.

---

## Success Criteria

All criteria must be met:

- [ ] `RunDSL` class implemented with proper type hints
- [ ] `run()` function implemented in `__init__.py`
- [ ] All components wire together correctly (Context, Registry, Backend, etc.)
- [ ] Tool registration works via DSL block/callable
- [ ] Example runs successfully and produces output
- [ ] Logger creates session files in `.boukensha/sessions/`
- [ ] Config, system prompt, model defaults work correctly
- [ ] Backend selection works for all backends
- [ ] API key selection works for all backends
- [ ] Code is compatible with Python 3.8+
- [ ] Type hints are comprehensive
- [ ] Code follows Python best practices (PEP 8)
- [ ] No regressions from Step 06 functionality

---

## Timeline Estimate

| Phase | Estimated Time | Complexity |
|-------|----------------|------------|
| Copy from 06_the_logger | 15 min | Trivial |
| Port RunDSL class | 20 min | Simple |
| Add run() function to __init__ | 1.5 hours | Medium |
| Port example.py | 30 min | Simple |
| Testing & validation | 45 min | Medium |
| Documentation updates | 20 min | Low |
| **Total** | **3-3.5 hours** | - |

**Note:** Most time is spent on the `run()` function which has significant logic for wiring components together. The actual amount of new code is small (~109 lines), but it requires careful translation of Ruby patterns to Python.

---

## Next Steps

**Ready to start!** Begin with:

```bash
# Copy entire 06_the_logger directory
cp -r week1_baseline/python/06_the_logger week1_baseline/python/07_the_run_dsl
cd week1_baseline/python/07_the_run_dsl
```

Then modify files in this order:

1. Create `boukensha/run_dsl.py` (NEW - 13 lines)
2. Modify `boukensha/__init__.py` (add imports + `run()` function - 60 new lines)
3. Modify `examples/example.py` (use DSL - 36 lines)
4. Update `README.md` to reflect Step 07
5. Test by running `python examples/example.py`

**Key files to reference:**
- `week1_baseline/ruby/07_the_run_dsl/lib/boukensha/run_dsl.rb` (13 lines)
- `week1_baseline/ruby/07_the_run_dsl/lib/boukensha.rb` (lines 55-111 for `run()` method)
- `week1_baseline/ruby/07_the_run_dsl/examples/example.rb` (36 lines)
