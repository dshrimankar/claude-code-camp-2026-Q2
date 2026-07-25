# Boukensha 01: Struct Skeleton - Python Port

This is a Python port of the Boukensha `01_struct_skeleton` step, which introduces the core data structures for building AI-driven MUD player agents.

## Overview

This step builds on the configuration system from `00_config` by adding three fundamental data structures:

- **Tool**: Represents an AI tool/function with schema and executable code
- **Message**: Represents a conversation message (user, assistant, or tool_result)
- **Context**: Manages complete state for API calls (messages, tools, system prompt)

These structures provide everything needed to interact with an LLM API, but no actual API calls are made yet—this is purely structural.

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
week1_baseline/python/01_struct_skeleton/
├── boukensha/
│   ├── __init__.py           # Module exports
│   ├── config.py             # Configuration system (from 00_config)
│   ├── tool.py               # Tool data structure
│   ├── message.py            # Message data structure
│   ├── context.py            # Context state manager
│   └── tasks/
│       ├── __init__.py       # Tasks module exports
│       ├── base.py           # Abstract base task
│       └── player.py         # Player task implementation
├── examples/
│   └── example.py            # Demonstration script
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Core Data Structures

### Tool

Represents an AI tool that the agent can call.

```python
from boukensha import Tool

def move_fn(args):
    return f"Moving {args['direction']}"

tool = Tool(
    name="move",
    description="Move the player in a direction",
    parameters={
        "direction": {
            "type": "string",
            "description": "north/south/east/west"
        }
    },
    block=move_fn
)
```

**Fields:**
- `name: str` - Unique identifier
- `description: str` - Human-readable description for the agent
- `parameters: Dict[str, Any]` - JSON schema for parameters
- `block: Callable[[Dict[str, Any]], Any]` - Executable function

### Message

Represents a single message in the conversation.

```python
from boukensha import Message

# User message
msg1 = Message(role="user", content="Explore the dungeon")

# Assistant message
msg2 = Message(role="assistant", content="I'll explore north")

# Tool result message
msg3 = Message(
    role="tool_result",
    content="You moved north",
    tool_use_id="tool_123"
)
```

**Fields:**
- `role: Literal["user", "assistant", "tool_result"]` - Message role
- `content: str` - Message content
- `tool_use_id: Optional[str]` - Links tool results to tool calls

### Context

Manages all state needed for an API call.

```python
from boukensha import Context, Config, Player, Tool

config = Config()
player_settings = config.tasks("player")
system_prompt = Player.system_prompt(
    player_settings,
    user_prompts_dir=config.user_prompts_dir,
    default_prompts_dir=Config.PROMPTS_DIR
)

ctx = Context(task=Player, system=system_prompt)

# Register tools
ctx.register_tool(some_tool)

# Add messages
ctx.add_message("user", "Hello!")
ctx.add_message("assistant", "Hi there!")

# Access state
print(f"Turns: {ctx.turn_count()}")
print(f"Tools: {ctx.tool_count()}")
```

**Properties:**
- `task: type[Base]` - Associated task class
- `system: Optional[str]` - System prompt
- `messages: List[Message]` - Conversation history
- `tools: Dict[str, Tool]` - Registered tools

**Methods:**
- `register_tool(tool: Tool)` - Register a tool
- `add_message(role, content, tool_use_id=None)` - Add a message
- `tool_count() -> int` - Number of registered tools
- `turn_count() -> int` - Number of user turns

## Usage Example

```python
from boukensha import Config, Context, Tool, Player

# Load configuration
config = Config()
player_settings = config.tasks("player")
system_prompt = Player.system_prompt(
    player_settings,
    user_prompts_dir=config.user_prompts_dir,
    default_prompts_dir=Config.PROMPTS_DIR
)

# Create context
ctx = Context(task=Player, system=system_prompt)

# Define and register a tool
def move_action(args):
    return f"You move {args['direction']} into a corridor."

move_tool = Tool(
    name="move",
    description="Move the player in a direction",
    parameters={
        "direction": {
            "type": "string",
            "description": "The direction to move"
        }
    },
    block=move_action
)
ctx.register_tool(move_tool)

# Build conversation
ctx.add_message("user", "Explore north")
ctx.add_message("assistant", "I'll head north")

# Inspect state
print(f"Context: {ctx}")
print(f"Tools: {list(ctx.tools.keys())}")
print(f"Messages: {len(ctx.messages)}")
```

## Running the Example

From the `week1_baseline` directory:

```bash
./bin/python/01_struct_skeleton
```

Or from the project root:

```bash
./week1_baseline/bin/python/01_struct_skeleton
```

Or directly:

```bash
cd week1_baseline/python/01_struct_skeleton
python3 examples/example.py
```

### Expected Output

```
=== Boukensha Step 1: Struct Skeleton ===

Config:   #<Boukensha::Config dir=/Users/you/.boukensha tasks=player>
Context:  #<Context task=player turns=2 tools=1>
Tool:     #<Tool name=move description=Move the player in a direction... params=['direction']>
Messages:
  #<Message role=user content=Explore north and tell me what you find....>
  #<Message role=assistant content=Sure, let me head north and take a look....>
```

## Type Hints

This port uses comprehensive type hints throughout:

```python
from typing import Callable, Dict, Any, Optional, List, Literal

@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    block: Callable[[Dict[str, Any]], Any]

@dataclass
class Message:
    role: Literal["user", "assistant", "tool_result"]
    content: str
    tool_use_id: Optional[str] = None

class Context:
    def __init__(self, task: type[Base], system: Optional[str] = None) -> None:
        ...
```

### Type Checking

Optional but recommended:

```bash
pip install mypy
mypy boukensha/ --strict
```

## Differences from Ruby Version

### Python Enhancements

1. **Comprehensive Type Hints**: Full type annotations using Python's `typing` module
2. **Dataclasses**: Used `@dataclass` for Tool and Message instead of Ruby Structs
3. **Literal Types**: Role validation with `Literal["user", "assistant", "tool_result"]`
4. **Property Decorators**: Used `@property` for Context attributes instead of `attr_reader`
5. **TYPE_CHECKING**: Avoided circular imports with conditional imports
6. **Docstrings**: Comprehensive documentation for all classes and methods

### Behavioral Equivalence

- ✅ Tool registration and storage works identically
- ✅ Message history management is the same
- ✅ Context state tracking (turn_count, tool_count) matches Ruby
- ✅ System prompt resolution works identically
- ✅ Configuration loading is the same
- ✅ String representation format matches Ruby output

### Implementation Details

**Ruby Struct vs Python Dataclass:**
```ruby
# Ruby
Tool = Struct.new(:name, :description, :parameters, :block)
```

```python
# Python
@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    block: Callable[[Dict[str, Any]], Any]
```

**Ruby attr_reader vs Python property:**
```ruby
# Ruby
class Context
  attr_reader :task, :system, :messages, :tools
end
```

```python
# Python
class Context:
    @property
    def task(self) -> type[Base]:
        return self._task
```

## Python 3.8 Compatibility

The code is compatible with Python 3.8+ using:

- `from __future__ import annotations` for forward references
- `typing.Dict`, `typing.List`, `typing.Optional` (not lowercase variants)
- `typing.Literal` (available in 3.8+)
- `typing.Callable` for function types
- `typing.TYPE_CHECKING` for import-time-only imports
- `dataclasses` (available since 3.7)

Avoids Python 3.9+ features like `dict | dict`, `list[str]`, or `str | None`.

## What's Next

This step provides the structural foundation. The next steps will:

1. Add actual LLM API integration
2. Implement tool execution
3. Build the agent loop
4. Add MUD connectivity

For now, this is purely about **structure and state management**—the building blocks for agent behavior.

## API Reference

### Tool

**Constructor:**
```python
Tool(name: str, description: str, parameters: Dict[str, Any], block: Callable)
```

**Example:**
```python
def my_fn(args: Dict[str, Any]) -> Any:
    return f"Result: {args['param']}"

tool = Tool(
    name="my_tool",
    description="Does something useful",
    parameters={"param": {"type": "string"}},
    block=my_fn
)
```

### Message

**Constructor:**
```python
Message(role: str, content: str, tool_use_id: Optional[str] = None)
```

**Example:**
```python
msg1 = Message("user", "Hello")
msg2 = Message("tool_result", "Done", tool_use_id="abc123")
```

### Context

**Constructor:**
```python
Context(task: type[Base], system: Optional[str] = None)
```

**Methods:**
- `register_tool(tool: Tool) -> None`
- `add_message(role: str, content: str, tool_use_id: Optional[str] = None) -> None`
- `tool_count() -> int`
- `turn_count() -> int`

**Example:**
```python
ctx = Context(task=Player, system="You are a helpful agent")
ctx.register_tool(my_tool)
ctx.add_message("user", "Do something")
print(ctx.turn_count())  # 1
```

## License

Same as the Ruby version.

## See Also

- Original Ruby implementation: `week1_baseline/ruby/01_struct_skeleton/`
- Port plan: `docs/plans/python_port/01_struct_skeleton`
- Previous step (config): `week1_baseline/python/00_config/`
