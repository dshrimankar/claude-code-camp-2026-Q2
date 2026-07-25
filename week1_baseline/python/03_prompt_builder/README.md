# Boukensha 03: Multi-Provider Prompt Builder - Python Port

This is a Python port of the Boukensha `03_prompt_builder` step, which introduces **multi-provider LLM support** through a serialization layer that converts internal agent state into provider-specific API formats.

## Overview

This step builds on `02_the_registry` by adding a prompt builder system that can serialize context (messages, tools, system prompt) into the specific format required by different LLM APIs:

- **PromptBuilder**: Facade class that delegates to provider-specific backends
- **Backend (abstract)**: Base class with model metadata, validation, and cost estimation
- **5 Provider Backends**:
  - `Anthropic` - Claude API (Messages API format)
  - `OpenAI` - GPT API (Chat Completions format)
  - `Gemini` - Google AI (GenerateContent format)
  - `Ollama` - Local Ollama instances
  - `OllamaCloud` - Ollama cloud service

This pattern allows the agent to remain provider-agnostic while supporting multiple LLM APIs.

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
python/03_prompt_builder/
├── boukensha/
│   ├── __init__.py              # Updated exports (v0.3.0)
│   ├── config.py                # Configuration system
│   ├── context.py               # Context state manager
│   ├── errors.py                # Custom exceptions (added UnsupportedModelError)
│   ├── message.py               # Message data structure
│   ├── registry.py              # Tool registry and dispatcher
│   ├── tool.py                  # Tool data structure
│   ├── prompt_builder.py        # NEW: Prompt builder facade
│   ├── backends/
│   │   ├── __init__.py          # NEW: Backend exports
│   │   ├── base.py              # NEW: Abstract backend base class
│   │   ├── anthropic.py         # NEW: Claude API backend
│   │   ├── openai.py            # NEW: GPT API backend
│   │   ├── gemini.py            # NEW: Google AI backend
│   │   ├── ollama.py            # NEW: Local Ollama backend
│   │   └── ollama_cloud.py      # NEW: Ollama Cloud backend
│   └── tasks/
│       ├── __init__.py
│       ├── base.py
│       └── player.py
├── examples/
│   └── example.py               # Multi-provider demonstration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## What's New in This Step

### 1. PromptBuilder Facade (`boukensha/prompt_builder.py`)

The PromptBuilder provides a uniform interface for building API requests:

```python
from boukensha import Context, Player, PromptBuilder
from boukensha.backends import Anthropic

# Setup context
ctx = Context(task=Player, system="You are a helpful agent")

# Create backend
backend = Anthropic(api_key="sk-ant-...", model="claude-sonnet-4-6")

# Create builder
builder = PromptBuilder(context=ctx, backend=backend)

# Get API payload
payload = builder.to_api_payload(max_output_tokens=2048)
headers = builder.headers
url = builder.url
```

**Key Methods:**
- `to_messages()` - Serialize messages to provider format
- `to_tools()` - Serialize tools to provider format
- `to_api_payload(max_output_tokens)` - Get complete API request payload
- `headers` - Get HTTP headers for the provider
- `url` - Get API endpoint URL

### 2. Backend Base Class (`boukensha/backends/base.py`)

The Backend base class provides:

```python
from abc import ABC, abstractmethod

class Base(ABC):
    # Model catalog with metadata
    MODELS: Dict[str, Dict[str, Any]] = {}

    # Model validation
    @classmethod
    def validate_model(cls, model: str) -> str: ...

    # Cost estimation
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> Optional[float]: ...

    # Abstract methods subclasses must implement
    @abstractmethod
    def to_messages(self, messages: List[Message]) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def to_tools(self, tools: Dict[str, Tool]) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def to_payload(self, context: Context, max_output_tokens: int) -> Dict[str, Any]: ...
```

**Model Metadata:**
```python
MODELS = {
    "claude-sonnet-4-6": {
        "context_window": 1_000_000,
        "cost_per_million": {"input": 3.0, "output": 15.0},
        "usage_unit": "tokens"
    }
}
```

### 3. Provider Backends

#### Anthropic Backend

**Format Characteristics:**
- System prompt separate from messages
- Simple message format: `{role, content}`
- Tools use `input_schema` format
- Tool results wrapped in content array

**Example:**
```python
from boukensha.backends import Anthropic

backend = Anthropic(
    api_key="sk-ant-...",
    model="claude-sonnet-4-6"
)

# Messages format
[
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
]

# Tools format
{
    "name": "move",
    "description": "Move the player",
    "input_schema": {
        "type": "object",
        "properties": {"direction": {"type": "string"}},
        "required": ["direction"]
    }
}
```

#### OpenAI Backend

**Format Characteristics:**
- System prompt goes in messages array as first message
- Tools wrapped in `{type: "function", function: {...}}`
- Tool results use `"tool"` role with `"tool_call_id"`
- Uses `"max_completion_tokens"` instead of `"max_tokens"`

**Example:**
```python
from boukensha.backends import OpenAI

backend = OpenAI(
    api_key="sk-...",
    model="gpt-5.4"
)

# Messages format (system in array)
[
    {"role": "system", "content": "You are a helpful agent"},
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
]

# Tools format
{
    "type": "function",
    "function": {
        "name": "move",
        "description": "Move the player",
        "parameters": {
            "type": "object",
            "properties": {"direction": {"type": "string"}},
            "required": ["direction"]
        }
    }
}
```

#### Gemini Backend

**Format Characteristics:**
- Uses `"model"` role instead of `"assistant"`
- Content wrapped in `parts` array with text objects
- Tool results use `functionResponse` format
- Tools in `functionDeclarations` wrapper
- System instruction has special format
- URL includes model name

**Example:**
```python
from boukensha.backends import Gemini

backend = Gemini(
    api_key="...",
    model="gemini-2.5-flash"
)

# Messages format
[
    {"role": "user", "parts": [{"text": "Hello"}]},
    {"role": "model", "parts": [{"text": "Hi there!"}]}
]

# Tools format
[{
    "functionDeclarations": [{
        "name": "move",
        "description": "Move the player",
        "parameters": {
            "type": "object",
            "properties": {"direction": {"type": "string"}},
            "required": ["direction"]
        }
    }]
}]
```

#### Ollama Backend

**Format Characteristics:**
- Local instances (no API key needed)
- System in messages array
- Tool results use `"tool_name"` instead of `"tool_call_id"`
- Includes `"stream": false` in payload
- Zero cost models (local compute)

**Example:**
```python
from boukensha.backends import Ollama

backend = Ollama(
    host="http://localhost:11434",  # Default
    model="gemma4:12b"
)

# Similar to OpenAI format but with local endpoint
```

#### OllamaCloud Backend

**Format Characteristics:**
- Similar to local Ollama but requires API key
- Cloud endpoint: `https://ollama.com/api/chat`
- Models have usage levels but no explicit pricing

**Example:**
```python
from boukensha.backends import OllamaCloud

backend = OllamaCloud(
    api_key="ollama-...",
    model="gemma4:31b-cloud"
)
```

## Running the Example

From the repository root:

```bash
./bin/python/03_prompt_builder
```

Or directly:

```bash
cd python/03_prompt_builder
python3 examples/example.py
```

### Expected Output

```
=== BOUKENSHA Step 3: Prompt Builder ===

Config: #<Boukensha::Config dir=/Users/you/.boukensha tasks=player>
Provider: anthropic
Model: claude-sonnet-4-6

API Payload:
{
  "model": "claude-sonnet-4-6",
  "system": "You are a helpful adventurer...",
  "max_tokens": 1024,
  "tools": [
    {
      "name": "look",
      "description": "Look around the current room for details",
      "input_schema": {
        "type": "object",
        "properties": {},
        "required": []
      }
    },
    {
      "name": "move",
      "description": "Move the player in a direction...",
      "input_schema": {
        "type": "object",
        "properties": {
          "direction": {
            "type": "string",
            "description": "The direction to move"
          }
        },
        "required": ["direction"]
      }
    }
  ],
  "messages": [
    {
      "role": "user",
      "content": "I just arrived in the dungeon. What's around me, and can you move north?"
    },
    {
      "role": "assistant",
      "content": "Let me take a look around first."
    },
    {
      "role": "user",
      "content": [
        {
          "type": "tool_result",
          "tool_use_id": "toolu_01X",
          "content": "A damp stone corridor stretches north. Torches flicker on the walls."
        }
      ]
    }
  ]
}
```

## Usage Examples

### Basic Usage

```python
from boukensha import Config, Context, Registry, Player, PromptBuilder
from boukensha.backends import Anthropic

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
registry.tool(
    name="move",
    description="Move the player",
    parameters={"direction": {"type": "string"}},
    block=lambda direction: f"You move {direction}"
)

# Add messages
ctx.add_message("user", "Move north")

# Create backend and builder
backend = Anthropic(api_key="sk-ant-...", model="claude-sonnet-4-6")
builder = PromptBuilder(context=ctx, backend=backend)

# Get API payload
payload = builder.to_api_payload(max_output_tokens=2048)
```

### Switching Providers

```python
# Just swap the backend!
from boukensha.backends import OpenAI, Gemini, Ollama

# OpenAI
backend = OpenAI(api_key="sk-...", model="gpt-5.4")
builder = PromptBuilder(context=ctx, backend=backend)

# Gemini
backend = Gemini(api_key="...", model="gemini-2.5-flash")
builder = PromptBuilder(context=ctx, backend=backend)

# Local Ollama
backend = Ollama(model="gemma4:12b")
builder = PromptBuilder(context=ctx, backend=backend)
```

### Cost Estimation

```python
backend = Anthropic(api_key="sk-ant-...", model="claude-sonnet-4-6")

# Estimate cost for a request
cost = backend.estimate_cost(
    input_tokens=1000,
    output_tokens=500
)
print(f"Estimated cost: ${cost:.4f}")
# Estimated cost: $0.0105

# Access model metadata
print(f"Context window: {backend.context_window}")
# Context window: 1000000

print(f"Input cost per M: ${backend.input_token_cost_per_million}")
# Input cost per M: $3.0
```

### Model Validation

```python
from boukensha.errors import UnsupportedModelError

try:
    backend = Anthropic(api_key="sk-ant-...", model="gpt-4")
except UnsupportedModelError as e:
    print(e)
    # Anthropic does not support model 'gpt-4'.
    # Supported models: claude-haiku-4-5, claude-sonnet-4-6, ...
```

## API Reference

### PromptBuilder

**Constructor:**
```python
PromptBuilder(context: Context, backend: Base)
```

**Methods:**

#### `to_messages() -> List[Dict[str, Any]]`
Serialize messages to provider format.

#### `to_tools() -> List[Dict[str, Any]]`
Serialize tools to provider format.

#### `to_api_payload(max_output_tokens: int = 1024) -> Dict[str, Any]`
Create complete API request payload.

**Properties:**
- `context: Context` - The context object
- `backend: Base` - The backend instance
- `headers: Dict[str, str]` - HTTP headers for API requests
- `url: str` - API endpoint URL

### Backend Base Class

**Class Methods:**

#### `validate_model(model: str) -> str`
Validate model is supported. Raises `UnsupportedModelError` if not.

#### `model_info(model: str) -> Optional[Dict[str, Any]]`
Get metadata for a specific model.

**Instance Methods:**

#### `estimate_cost(input_tokens: int, output_tokens: int) -> Optional[float]`
Estimate request cost in USD.

**Properties:**
- `model: str` - Current model name
- `context_window: int` - Maximum context size
- `input_token_cost_per_million: float` - Input token pricing
- `output_token_cost_per_million: float` - Output token pricing
- `usage_unit: str` - Usage unit (e.g., "tokens", "local_compute")

**Abstract Methods:**
- `to_messages(messages)` - Serialize messages
- `to_tools(tools)` - Serialize tools
- `to_payload(context, max_output_tokens)` - Create API payload
- `headers` - Get HTTP headers
- `url` - Get API endpoint

## Provider Comparison

| Feature | Anthropic | OpenAI | Gemini | Ollama | OllamaCloud |
|---------|-----------|--------|--------|--------|-------------|
| System in messages | ❌ Separate | ✅ First msg | ❌ Separate | ✅ First msg | ✅ First msg |
| Assistant role | `assistant` | `assistant` | `model` | `assistant` | `assistant` |
| Tool wrapper | None | `function` | `functionDeclarations` | `function` | `function` |
| Tool result role | `user` | `tool` | `user` | `tool` | `tool` |
| Tool result ID | `tool_use_id` | `tool_call_id` | `name` | `tool_name` | `tool_name` |
| API Key | Required | Required | Required | ❌ None | Required |
| Cost | Paid | Paid | Paid | Free (local) | Usage-based |

## Type Hints

This port uses comprehensive type hints throughout:

```python
from typing import Dict, Any, List, Optional
from boukensha.backends.base import Base

class PromptBuilder:
    def __init__(self, context: Context, backend: Base) -> None: ...

    def to_api_payload(
        self, max_output_tokens: int = 1024
    ) -> Dict[str, Any]: ...
```

### Type Checking

Optional but recommended:

```bash
pip install mypy
mypy boukensha/ --strict
```

## Differences from Ruby Version

### Python Advantages

1. **Simpler Dictionary Access**:
   - Ruby: `model_info.fetch(:context_window)`
   - Python: `model_info["context_window"]`

2. **No Symbol Conversion**:
   - Ruby requires converting between strings and symbols
   - Python uses strings consistently

3. **f-strings**:
   - Ruby: `"Bearer #{@api_key}"`
   - Python: `f"Bearer {self._api_key}"`

### Implementation Equivalence

- ✅ All 5 backends implemented
- ✅ Model metadata and validation
- ✅ Cost estimation
- ✅ Provider-specific serialization
- ✅ PromptBuilder facade
- ✅ All functionality preserved

## Architectural Insights

### Why This Pattern Matters

The PromptBuilder pattern is essential for multi-provider LLM systems:

1. **Provider Agnostic**: Agent logic doesn't know or care which LLM it's using
2. **Format Isolation**: Each provider's quirks are isolated in its backend
3. **Easy Migration**: Switch providers by changing one line of code
4. **Cost Tracking**: Built-in model metadata for cost estimation
5. **Model Validation**: Prevents using unsupported models

### Design Benefits

- **Facade Pattern**: PromptBuilder provides uniform interface
- **Strategy Pattern**: Backends are interchangeable strategies
- **Open/Closed**: Add new providers without changing existing code
- **Single Responsibility**: Each backend handles one provider

## Python 3.8 Compatibility

The code is compatible with Python 3.8+ using:

- `from __future__ import annotations` for forward references
- `typing.Dict`, `typing.List`, `typing.Optional` (not lowercase)
- `typing.TYPE_CHECKING` for circular import avoidance
- No Python 3.9+ features like `dict | dict` or `str | None`

## What's Next

This step provides the serialization foundation. Future steps will:

1. Add actual LLM API integration (HTTP requests)
2. Implement response parsing and tool use extraction
3. Build the complete agent loop
4. Add MUD connectivity and live interaction

For now, this is about **provider-specific serialization** - converting context to API-ready payloads.

## See Also

- Original Ruby implementation: `ruby/03_prompt_builder/`
- Port plan: `docs/plans/python_port/03_prompt_builder`
- Previous step: `python/02_the_registry/`
