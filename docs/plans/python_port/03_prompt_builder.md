# Port Plan: 03_prompt_builder (Ruby ’ Python)

## Overview

This step introduces **multi-provider LLM support** by adding a serialization layer that converts the internal agent state (Context) into provider-specific API formats.

**New Components:**
- `PromptBuilder` - Facade class for building prompts
- `Backend` (abstract) - Base class for provider serializers
- 5 Backend implementations:
  - `AnthropicBackend` - Claude API format
  - `OpenAIBackend` - GPT API format
  - `GeminiBackend` - Google AI format
  - `OllamaBackend` - Ollama local format
  - `OllamaCloudBackend` - Ollama cloud format
- Model metadata system with pricing and validation

**Estimated Effort:** 7-10 hours
**New Lines of Code:** ~925 lines (620 new + 305 copied from previous step)

## What's New in This Step

### 1. PromptBuilder Class (`lib/boukensha/prompt_builder.rb`)

The PromptBuilder is a facade that delegates to backend-specific serializers:

```ruby
# Ruby
module Boukensha
  class PromptBuilder
    attr_reader :context, :backend

    def initialize(context:, backend:)
      @context = context
      @backend = backend
    end

    def system = backend.system
    def messages = backend.messages
    def tools = backend.tools
    def model = backend.model
    def max_tokens = backend.max_tokens

    def to_h
      {
        model: model,
        max_tokens: max_tokens,
        system: system,
        messages: messages,
        tools: tools
      }
    end
  end
end
```

**Python Translation:**
```python
# Python (boukensha/prompt_builder.py)
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List

if TYPE_CHECKING:
    from boukensha.context import Context
    from boukensha.backends.base import Backend

class PromptBuilder:
    """Facade for building LLM API requests from context."""

    def __init__(self, context: Context, backend: Backend) -> None:
        self._context = context
        self._backend = backend

    @property
    def context(self) -> Context:
        return self._context

    @property
    def backend(self) -> Backend:
        return self._backend

    @property
    def system(self) -> str:
        return self._backend.system

    @property
    def messages(self) -> List[Dict[str, Any]]:
        return self._backend.messages

    @property
    def tools(self) -> List[Dict[str, Any]]:
        return self._backend.tools

    @property
    def model(self) -> str:
        return self._backend.model

    @property
    def max_tokens(self) -> int:
        return self._backend.max_tokens

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to API request format."""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": self.system,
            "messages": self.messages,
            "tools": self.tools
        }

    def __repr__(self) -> str:
        backend_name = self._backend.__class__.__name__
        tool_count = len(self._context.tools)
        msg_count = len(self._context.messages)
        return (
            f"#<PromptBuilder backend={backend_name} "
            f"model={self.model} tools={tool_count} messages={msg_count}>"
        )
```

### 2. Backend Abstract Base Class (`lib/boukensha/backends/backend.rb`)

The Backend provides model metadata and validation:

```ruby
# Ruby
module Boukensha
  module Backends
    class Backend
      MODELS = {}.freeze

      attr_reader :context

      def initialize(context:, model: nil)
        @context = context
        @model = model || default_model
        validate_model!(@model)
      end

      def model = @model

      def system
        raise NotImplementedError, "Subclass must implement #system"
      end

      def messages
        raise NotImplementedError, "Subclass must implement #messages"
      end

      def tools
        raise NotImplementedError, "Subclass must implement #tools"
      end

      def max_tokens
        raise NotImplementedError, "Subclass must implement #max_tokens"
      end

      private

      def default_model
        self.class::MODELS.keys.first
      end

      def validate_model!(model)
        unless self.class::MODELS.key?(model)
          raise ArgumentError, "Unknown model: #{model}"
        end
      end
    end
  end
end
```

**Python Translation:**
```python
# Python (boukensha/backends/base.py)
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Any, List, TypedDict, Optional

if TYPE_CHECKING:
    from boukensha.context import Context

class ModelMetadata(TypedDict, total=False):
    """Metadata for a specific model."""
    max_tokens: int
    cost_per_mtok_input: float
    cost_per_mtok_output: float
    supports_tools: bool
    supports_vision: bool

class Backend(ABC):
    """Abstract base class for LLM provider backends."""

    # Subclasses must override this with their model catalog
    MODELS: Dict[str, ModelMetadata] = {}

    def __init__(self, context: Context, model: Optional[str] = None) -> None:
        self._context = context
        self._model = model or self._default_model()
        self._validate_model(self._model)

    @property
    def context(self) -> Context:
        return self._context

    @property
    def model(self) -> str:
        return self._model

    @property
    @abstractmethod
    def system(self) -> str:
        """Return system prompt in provider format."""
        ...

    @property
    @abstractmethod
    def messages(self) -> List[Dict[str, Any]]:
        """Return messages in provider format."""
        ...

    @property
    @abstractmethod
    def tools(self) -> List[Dict[str, Any]]:
        """Return tools in provider format."""
        ...

    @property
    @abstractmethod
    def max_tokens(self) -> int:
        """Return max tokens for this model."""
        ...

    def _default_model(self) -> str:
        """Get the default model for this backend."""
        if not self.MODELS:
            raise ValueError(f"{self.__class__.__name__} has no MODELS defined")
        return next(iter(self.MODELS.keys()))

    def _validate_model(self, model: str) -> None:
        """Validate that the model is supported."""
        if model not in self.MODELS:
            available = ", ".join(self.MODELS.keys())
            raise ValueError(
                f"Unknown model: {model}. "
                f"Available models: {available}"
            )
```

### 3. AnthropicBackend (`lib/boukensha/backends/anthropic.rb`)

Claude API format - the reference implementation:

```ruby
# Ruby (simplified)
module Boukensha
  module Backends
    class Anthropic < Backend
      MODELS = {
        "claude-3-5-sonnet-20241022" => {
          max_tokens: 8192,
          cost_per_mtok_input: 3.00,
          cost_per_mtok_output: 15.00,
          supports_tools: true
        },
        # ... more models
      }.freeze

      def system
        context.system
      end

      def messages
        context.messages.map { |msg| serialize_message(msg) }
      end

      def tools
        context.tools.values.map { |tool| serialize_tool(tool) }
      end

      def max_tokens
        self.class::MODELS.dig(model, :max_tokens)
      end

      private

      def serialize_message(msg)
        { role: msg.role, content: msg.content }
      end

      def serialize_tool(tool)
        {
          name: tool.name,
          description: tool.description,
          input_schema: {
            type: "object",
            properties: tool.parameters,
            required: tool.parameters.keys
          }
        }
      end
    end
  end
end
```

**Python Translation:**
```python
# Python (boukensha/backends/anthropic.py)
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List

from boukensha.backends.base import Backend, ModelMetadata

if TYPE_CHECKING:
    from boukensha.context import Context
    from boukensha.message import Message
    from boukensha.tool import Tool

class AnthropicBackend(Backend):
    """Anthropic Claude API format serializer."""

    MODELS: Dict[str, ModelMetadata] = {
        "claude-3-5-sonnet-20241022": {
            "max_tokens": 8192,
            "cost_per_mtok_input": 3.00,
            "cost_per_mtok_output": 15.00,
            "supports_tools": True,
            "supports_vision": True,
        },
        "claude-3-5-haiku-20241022": {
            "max_tokens": 8192,
            "cost_per_mtok_input": 1.00,
            "cost_per_mtok_output": 5.00,
            "supports_tools": True,
            "supports_vision": False,
        },
        # Add other Claude models as needed
    }

    @property
    def system(self) -> str:
        return self._context.system

    @property
    def messages(self) -> List[Dict[str, Any]]:
        return [self._serialize_message(msg) for msg in self._context.messages]

    @property
    def tools(self) -> List[Dict[str, Any]]:
        return [self._serialize_tool(tool) for tool in self._context.tools.values()]

    @property
    def max_tokens(self) -> int:
        return self.MODELS[self._model]["max_tokens"]

    def _serialize_message(self, msg: Message) -> Dict[str, Any]:
        """Serialize message to Anthropic format."""
        return {
            "role": msg.role,
            "content": msg.content
        }

    def _serialize_tool(self, tool: Tool) -> Dict[str, Any]:
        """Serialize tool to Anthropic format."""
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": {
                "type": "object",
                "properties": tool.parameters,
                "required": list(tool.parameters.keys())
            }
        }
```

### 4. OpenAIBackend (`lib/boukensha/backends/openai.rb`)

OpenAI GPT API format - system goes in messages array:

```ruby
# Ruby key differences
def messages
  # System goes in messages array for OpenAI
  sys = [{ role: "system", content: context.system }]
  msgs = context.messages.map { |msg| serialize_message(msg) }
  sys + msgs
end

def serialize_tool(tool)
  {
    type: "function",
    function: {
      name: tool.name,
      description: tool.description,
      parameters: {
        type: "object",
        properties: tool.parameters,
        required: tool.parameters.keys
      }
    }
  }
end
```

**Python Translation:**
```python
# Python (boukensha/backends/openai.py)
@property
def messages(self) -> List[Dict[str, Any]]:
    """OpenAI puts system in messages array."""
    system_msg = [{"role": "system", "content": self._context.system}]
    user_msgs = [self._serialize_message(msg) for msg in self._context.messages]
    return system_msg + user_msgs

def _serialize_tool(self, tool: Tool) -> Dict[str, Any]:
    """OpenAI wraps tools in 'function' object."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": tool.parameters,
                "required": list(tool.parameters.keys())
            }
        }
    }
```

### 5. GeminiBackend (`lib/boukensha/backends/gemini.rb`)

Google AI format - uses "user"/"model" roles instead of "user"/"assistant":

```ruby
# Ruby key differences
def serialize_message(msg)
  role = msg.role == "assistant" ? "model" : "user"
  { role: role, parts: [{ text: msg.content }] }
end

def serialize_tool(tool)
  {
    function_declarations: [{
      name: tool.name,
      description: tool.description,
      parameters: {
        type: "OBJECT",
        properties: tool.parameters,
        required: tool.parameters.keys
      }
    }]
  }
end
```

**Python Translation:**
```python
# Python (boukensha/backends/gemini.py)
def _serialize_message(self, msg: Message) -> Dict[str, Any]:
    """Gemini uses 'model' instead of 'assistant'."""
    role = "model" if msg.role == "assistant" else "user"
    return {
        "role": role,
        "parts": [{"text": msg.content}]
    }

def _serialize_tool(self, tool: Tool) -> Dict[str, Any]:
    """Gemini uses function_declarations format."""
    return {
        "function_declarations": [{
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "OBJECT",
                "properties": tool.parameters,
                "required": list(tool.parameters.keys())
            }
        }]
    }
```

### 6. OllamaBackend and OllamaCloudBackend

Both use similar formats with minor differences in model naming.

## Directory Structure

```
week1_baseline/python/03_prompt_builder/
   boukensha/
      __init__.py              # Updated exports
      config.py                # From 02_the_registry
      context.py               # From 02_the_registry
      errors.py                # From 02_the_registry
      message.py               # From 02_the_registry
      registry.py              # From 02_the_registry
      tool.py                  # From 02_the_registry
      prompt_builder.py        # NEW: Prompt builder facade
      backends/
         __init__.py          # NEW: Backend exports
         base.py              # NEW: Abstract backend
         anthropic.py         # NEW: Claude API format
         openai.py            # NEW: GPT API format
         gemini.py            # NEW: Google AI format
         ollama.py            # NEW: Ollama local format
         ollama_cloud.py      # NEW: Ollama cloud format
      tasks/
          __init__.py
          base.py
          player.py
   examples/
      example.py               # NEW: Multi-provider demo
   requirements.txt             # Same dependencies
   README.md                    # NEW: Documentation
```

## Implementation Phases

### Phase 1: Setup and Base Classes (2-3 hours)

1. **Copy from 02_the_registry:**
   - All files from `python/02_the_registry/boukensha/`
   - requirements.txt
   - bin script

2. **Create backends module structure:**
   ```bash
   mkdir -p boukensha/backends
   touch boukensha/backends/__init__.py
   ```

3. **Implement base.py:**
   - `Backend` abstract class
   - `ModelMetadata` TypedDict
   - Model validation logic
   - Abstract methods for system, messages, tools, max_tokens

### Phase 2: PromptBuilder Facade (1 hour)

1. **Create prompt_builder.py:**
   - `PromptBuilder` class
   - Properties delegating to backend
   - `to_dict()` method for serialization
   - `__repr__()` for debugging

### Phase 3: Provider Backends (3-4 hours)

1. **AnthropicBackend** (reference implementation):
   - Model catalog with pricing
   - Direct serialization (simplest format)
   - Test with example

2. **OpenAIBackend**:
   - System-in-messages pattern
   - Function wrapping for tools
   - Model catalog

3. **GeminiBackend**:
   - Role translation (assistant ’ model)
   - Parts format for content
   - OBJECT type for parameters

4. **OllamaBackend & OllamaCloudBackend**:
   - Similar to OpenAI format
   - Local vs cloud model naming

### Phase 4: Example and Testing (1-2 hours)

1. **Create example.py:**
   - Demonstrate all 5 backends
   - Show serialization differences
   - Compare output formats

2. **Test each backend:**
   - Verify model validation
   - Check serialization correctness
   - Ensure pricing metadata present

### Phase 5: Documentation (1 hour)

1. **Create comprehensive README.md:**
   - Overview of multi-provider support
   - Usage examples for each backend
   - API reference
   - Provider format comparison table
   - Type hints documentation

2. **Update __init__.py:**
   - Export PromptBuilder
   - Export all backends
   - Export Backend base class

## Key Python Patterns

### 1. TypedDict for Model Metadata

```python
from typing import TypedDict

class ModelMetadata(TypedDict, total=False):
    max_tokens: int
    cost_per_mtok_input: float
    cost_per_mtok_output: float
    supports_tools: bool
    supports_vision: bool
```

### 2. Abstract Base Class

```python
from abc import ABC, abstractmethod

class Backend(ABC):
    @property
    @abstractmethod
    def system(self) -> str:
        ...
```

### 3. Property Delegation

```python
class PromptBuilder:
    @property
    def system(self) -> str:
        return self._backend.system
```

### 4. Dict.get() for Safe Access

```python
# Ruby: MODELS.dig(model, :max_tokens)
# Python: self.MODELS[self._model]["max_tokens"]
# Or safer: self.MODELS[self._model].get("max_tokens", 8192)
```

## Testing Strategy

For each backend, verify:

1. **Model validation:**
   ```python
   # Should raise ValueError
   backend = AnthropicBackend(ctx, model="nonexistent-model")
   ```

2. **System serialization:**
   ```python
   assert backend.system == ctx.system
   ```

3. **Message format:**
   ```python
   messages = backend.messages
   assert isinstance(messages, list)
   assert all("role" in m and "content" in m for m in messages)
   ```

4. **Tool format:**
   ```python
   tools = backend.tools
   assert isinstance(tools, list)
   # Check provider-specific structure
   ```

5. **Max tokens:**
   ```python
   assert backend.max_tokens > 0
   ```

## Ruby vs Python Differences

### 1. Hash Access

**Ruby:**
```ruby
MODELS.dig(model, :max_tokens)
```

**Python:**
```python
self.MODELS[self._model]["max_tokens"]
# Or with default:
self.MODELS[self._model].get("max_tokens", 8192)
```

### 2. Symbol Keys vs String Keys

**Ruby:** Uses symbols (`:max_tokens`)
**Python:** Uses strings (`"max_tokens"`)

### 3. Method Names

**Ruby:** `to_h` (convert to Hash)
**Python:** `to_dict()` (convert to dict)

### 4. Abstract Methods

**Ruby:**
```ruby
def system
  raise NotImplementedError, "Subclass must implement #system"
end
```

**Python:**
```python
@property
@abstractmethod
def system(self) -> str:
    ...
```

## Expected Output

```
=== BOUKENSHA Step 3: Multi-Provider Prompt Builder ===

Anthropic Backend:
  Model: claude-3-5-sonnet-20241022
  Max Tokens: 8192
  System: You are a helpful adventurer...
  Messages: [{'role': 'user', 'content': 'Hello'}]
  Tools: [{'name': 'move', 'description': '...', 'input_schema': {...}}]

OpenAI Backend:
  Model: gpt-4-turbo-preview
  Max Tokens: 4096
  Messages: [
    {'role': 'system', 'content': 'You are a helpful adventurer...'},
    {'role': 'user', 'content': 'Hello'}
  ]
  Tools: [{'type': 'function', 'function': {'name': 'move', ...}}]

Gemini Backend:
  Model: gemini-1.5-pro
  Max Tokens: 8192
  Messages: [{'role': 'user', 'parts': [{'text': 'Hello'}]}]
  Tools: [{'function_declarations': [{'name': 'move', ...}]}]

[Similar output for Ollama backends...]
```

## Validation Checklist

- [ ] All 5 backends implemented
- [ ] Backend abstract base class complete
- [ ] PromptBuilder facade working
- [ ] Model validation for all backends
- [ ] Comprehensive type hints throughout
- [ ] Example demonstrates all providers
- [ ] README documents all formats
- [ ] Python 3.8+ compatible
- [ ] No dependencies on previous step imports

## Timeline Estimate

- **Phase 1 (Setup):** 2-3 hours
- **Phase 2 (PromptBuilder):** 1 hour
- **Phase 3 (Backends):** 3-4 hours
- **Phase 4 (Example):** 1-2 hours
- **Phase 5 (Documentation):** 1 hour

**Total:** 7-10 hours

## Success Criteria

1. All 5 backends serialize context correctly
2. Provider-specific formats match Ruby output
3. Model validation prevents invalid models
4. Type hints pass mypy --strict
5. Example runs without errors
6. Documentation complete and accurate

## Notes

- This step is pure serialization - no LLM API calls yet
- Each backend is independent - can implement in parallel
- Anthropic backend is the reference (simplest format)
- Future steps will use these backends for actual API calls
- Model metadata will be used for cost tracking later
