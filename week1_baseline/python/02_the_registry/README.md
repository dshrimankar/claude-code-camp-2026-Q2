# Boukensha 02: Tool Registry - Python Port

This is a Python port of the Boukensha `02_the_registry` step, which introduces the **Tool Registry Pattern** - a central dispatcher for managing tool registration and execution.

## Overview

This step builds on `01_struct_skeleton` by adding an indirection layer between the agent and tool implementations:

- **Registry**: Central manager for tool registration and dispatch
- **UnknownToolError**: Custom exception raised when dispatching non-existent tools
- **Tool Dispatch Pattern**: Agent never calls tools directly; registry routes requests

This pattern simulates how real LLM agents work: the model outputs JSON tool use requests, and the harness (Registry) looks up and executes the appropriate tool.

## Requirements

- Python 3.8+
- PyYAML
- python-dotenv

## Installation

```bash
pip install -r requirements.txt
```

Or on macOS with system-managed Python:

```bash
python3 -m pip install --break-system-packages PyYAML python-dotenv
```

## Directory Structure

```
week1_baseline/python/02_the_registry/
├── boukensha/
│   ├── __init__.py           # Module exports (updated)
│   ├── config.py             # Configuration system (from 01)
│   ├── context.py            # Context state manager (from 01)
│   ├── message.py            # Message data structure (from 01)
│   ├── tool.py               # Tool data structure (from 01)
│   ├── registry.py           # NEW: Tool registry and dispatcher
│   ├── errors.py             # NEW: Custom exceptions
│   └── tasks/
│       ├── __init__.py       # Tasks module exports
│       ├── base.py           # Abstract base task
│       └── player.py         # Player task implementation
├── examples/
│   └── example.py            # Demonstration script
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## What's New in This Step

### Registry Class (`boukensha/registry.py`)

The Registry provides a central point for tool registration and dispatch:

```python
from boukensha import Registry, Context, Player

# Create context and registry
ctx = Context(task=Player, system="You are a helpful agent")
registry = Registry(ctx)

# Register a tool
def move_fn(direction: str) -> str:
    return f"Moving {direction}"

registry.tool(
    name="move",
    description="Move the player in a direction",
    parameters={"direction": {"type": "string"}},
    block=move_fn
)

# Dispatch a tool
result = registry.dispatch("move", {"direction": "north"})
print(result)  # "Moving north"
```

**Key Methods:**
- `tool(name, description, parameters, block)` - Register a tool
- `dispatch(name, args)` - Execute a tool by name

### UnknownToolError Exception (`boukensha/errors.py`)

Raised when attempting to dispatch a tool that doesn't exist:

```python
from boukensha.errors import UnknownToolError

try:
    registry.dispatch("nonexistent_tool")
except UnknownToolError as e:
    print(f"Error: {e}")
    # Error: No tool registered as 'nonexistent_tool'
```

## Usage Example

```python
from boukensha import Config, Context, Registry, Player, UnknownToolError

# Setup
config = Config()
player_settings = config.tasks("player")
system_prompt = Player.system_prompt(
    player_settings,
    user_prompts_dir=config.user_prompts_dir,
    default_prompts_dir=Config.PROMPTS_DIR
)

ctx = Context(task=Player, system=system_prompt)
registry = Registry(ctx)

# Register tools
def move_fn(direction: str) -> str:
    return f"You move {direction} into a corridor."

def shout_fn(message: str) -> str:
    return message.upper()

registry.tool(
    name="move",
    description="Move the player",
    parameters={"direction": {"type": "string"}},
    block=move_fn
)

registry.tool(
    name="shout",
    description="Shout a message",
    parameters={"message": {"type": "string"}},
    block=shout_fn
)

# Dispatch tools
result = registry.dispatch("move", {"direction": "north"})
print(result)  # "You move north into a corridor."

result = registry.dispatch("shout", {"message": "hello"})
print(result)  # "HELLO"

# Error handling
try:
    registry.dispatch("flee")  # This tool doesn't exist
except UnknownToolError as e:
    print(f"Caught: {e}")
```

## Running the Example

From the `week1_baseline` directory:

```bash
./bin/python/02_the_registry
```

Or from the project root:

```bash
./week1_baseline/bin/python/02_the_registry
```

Or directly:

```bash
cd week1_baseline/python/02_the_registry
python3 examples/example.py
```

### Expected Output

```
=== BOUKENSHA Step 2: Tool Registry ===

Config:  #<Boukensha::Config dir=/Users/you/.boukensha tasks=player>
Context: #<Context task=player turns=0 tools=2>
Tools:
  #<Tool name=move description=Move the player in a direction... params=['direction']>
  #<Tool name=shout description=Shout a message so everyone in... params=['message']>

Dispatching 'shout' with message='dragon spotted'...
Result: DRAGON SPOTTED

Dispatching 'move' with direction='north'...
Result: You move north into a torch-lit corridor.

UnknownToolError caught: No tool registered as 'flee'
```

## API Reference

### Registry

**Constructor:**
```python
Registry(context: Context)
```

**Methods:**

#### `tool(name, description, parameters=None, block=None)`

Register a tool with the registry.

- **name** (str): Unique tool identifier
- **description** (str): Human-readable description for the agent
- **parameters** (Dict[str, Any], optional): JSON schema for parameters (defaults to {})
- **block** (Callable, optional): Function to execute when tool is invoked

**Raises:**
- `ValueError`: If block is None

**Example:**
```python
def my_tool(arg: str) -> str:
    return f"Result: {arg}"

registry.tool(
    name="my_tool",
    description="Does something useful",
    parameters={"arg": {"type": "string"}},
    block=my_tool
)
```

#### `dispatch(name, args=None)`

Dispatch a tool call by name with arguments.

- **name** (str): Name of the tool to execute
- **args** (Dict[str, Any], optional): Arguments to pass (defaults to {})

**Returns:** The result of executing the tool

**Raises:**
- `UnknownToolError`: If no tool with the given name exists

**Example:**
```python
result = registry.dispatch("my_tool", {"arg": "value"})
```

### UnknownToolError

Custom exception raised when dispatching a non-existent tool.

**Usage:**
```python
try:
    registry.dispatch("missing_tool")
except UnknownToolError as e:
    print(f"Error: {e}")
```

## Type Hints

This port uses comprehensive type hints throughout:

```python
from typing import Callable, Dict, Any, Optional

class Registry:
    def __init__(self, context: Context) -> None: ...

    def tool(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        block: Optional[Callable[..., Any]] = None,
    ) -> None: ...

    def dispatch(
        self,
        name: str,
        args: Optional[Dict[str, Any]] = None
    ) -> Any: ...
```

### Type Checking

Optional but recommended:

```bash
pip install mypy
mypy boukensha/ --strict
```

## Differences from Ruby Version

### Python Advantages

1. **No Symbol Key Transformation**:
   - Ruby requires `args.transform_keys(&:to_sym)` to convert string keys to symbols
   - Python uses strings for all dict keys - no transformation needed!

2. **Simpler Callable Handling**:
   - Ruby: `block.call(**args)`
   - Python: `block(**args)` - same, but no special syntax needed

3. **Exception Handling**:
   - Very similar in both languages
   - Both use try/except (Ruby: begin/rescue)

### Implementation Equivalence

- ✅ Registry stores tools in Context (same as Ruby)
- ✅ `tool()` method creates and registers tools
- ✅ `dispatch()` looks up and executes tools
- ✅ UnknownToolError raised for missing tools
- ✅ All functionality preserved

### Ruby vs Python: Key Differences

**Ruby:**
```ruby
# Blocks use symbol keys
registry.tool("move", ...) do |direction:|
  "Moving #{direction}"
end

# String keys transformed to symbols before calling
registry.dispatch("move", { "direction" => "north" })
# Internally: tool.block.call(**{ direction: "north" })
```

**Python:**
```python
# Functions use regular parameters
def move_fn(direction: str) -> str:
    return f"Moving {direction}"

registry.tool(name="move", ..., block=move_fn)

# String keys work directly
registry.dispatch("move", {"direction": "north"})
# Internally: tool.block(**{"direction": "north"})
```

## Architectural Insights

### Why This Pattern Matters

The Registry pattern is foundational for LLM agent systems:

1. **Decoupling**: Agent logic is separate from tool implementation
2. **API Compatibility**: Bridges JSON (LLM output) to function calls
3. **Error Boundaries**: Explicit handling of missing/invalid tools
4. **Extensibility**: Foundation for middleware, validation, logging
5. **Multi-Agent**: Different agents can have different tool sets

### From the Design Notes:

> "The agent NEVER calls a tool directly. It emits a structured request (name and args) and the Registry looks up the tool and runs it."

This simulates real LLM behavior where the model outputs tool use requests as JSON.

### Current Architecture Note

The README notes an architectural consideration:

> "We now register tools with the Registry but our code still has direct registration and tools in context. This likely should have been reworked... The context should have reference to tools[] it's currently using, and the full table of tools registered should live on the Registry."

This is intentionally left as-is for learning purposes and will be addressed in future steps.

## Python 3.8 Compatibility

The code is compatible with Python 3.8+ using:

- `from __future__ import annotations` for forward references
- `typing.Dict`, `typing.Optional`, `typing.Any`, `typing.Callable` (not lowercase)
- No Python 3.9+ features like `dict | dict` or `str | None`

## What's Next

This step provides the dispatch pattern foundation. Future steps will:

1. Add actual LLM API integration
2. Implement agent decision-making (when to call which tool)
3. Build the complete agent loop
4. Add MUD connectivity and live interaction

For now, this is about **the dispatch pattern** - the indirection layer between agent requests and tool execution.

## See Also

- Original Ruby implementation: `week1_baseline/ruby/02_the_registry/`
- Port plan: `docs/plans/python_port/02_the_registry`
- Previous step: `week1_baseline/python/01_struct_skeleton/`
