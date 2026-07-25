# Port Plan: 05_agent_loop (Ruby → Python)

## Overview

This step introduces the **Agent Loop** - the heart of Boukensha. Everything built before this (structs, registry, prompt builder, client) was setup. The loop is where the agent actually does work.

**New Components:**
- `Agent` - The agent loop that sends requests, dispatches tools, and knows when to stop
- `LoopError` - Exception for runaway agents
- Response parsing in all backends (normalize different provider formats)
- `assistant_message` methods in backends (rebuild provider-specific format from normalized content)
- `max_iterations` and `max_output_tokens` configuration methods

**Estimated Effort:** 6-8 hours
**New Lines of Code:** ~400 lines (Agent + backend updates + example)

## What's New in This Step

### 1. Agent Class (`lib/boukensha/agent.rb`)

The Agent implements the tool-use loop:

```ruby
# Ruby
module Boukensha
  class Agent
    MAX_ITERATIONS = 25
    WRAP_UP_OUTPUT_TOKENS = 400
    WRAP_UP_DIRECTIVE = <<~MSG.strip
      You have reached your action limit for this turn. Do not call any more tools.
      Briefly summarize what you accomplished, what is still unfinished, and the
      single next action you would take.
    MSG

    def initialize(context:, registry:, builder:, client:,
                   task_settings: nil, max_iterations: nil, max_output_tokens: nil)
      @context = context
      @registry = registry
      @builder = builder
      @client = client
      @max_iterations = resolve_max_iterations(task_settings, max_iterations)
      @max_output_tokens = resolve_max_output_tokens(task_settings, max_output_tokens)
      @iteration = 0
    end

    def run
      loop do
        return wrap_up("max_iterations") if iteration_limit_reached?

        @iteration += 1
        puts "[iteration #{@iteration}/#{@max_iterations}]"

        response = @client.call(**call_opts)
        parsed   = @builder.parse_response(response)

        if parsed[:stop_reason] == "tool_use"
          handle_tool_calls(parsed[:content])
        else
          return extract_text(parsed[:content])
        end
      end
    end

    private

    def handle_tool_calls(content)
      @context.add_message(:assistant, content)

      content.select { |b| b["type"] == "tool_use" }.each do |block|
        name   = block["name"]
        args   = block["input"]
        use_id = block["id"]

        puts "  tool call → #{name}(#{args})"
        result = @registry.dispatch(name, args)
        puts "  tool result → #{result.to_s[0..60]}"

        @context.add_message(:tool_result, result.to_s, tool_use_id: use_id)
      end
    end

    def extract_text(content)
      content.select { |b| b["type"] == "text" }.map { |b| b["text"] }.join
    end
  end
end
```

**Python Translation:**
```python
# Python (boukensha/agent.py)
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List, Optional

if TYPE_CHECKING:
    from boukensha.context import Context
    from boukensha.registry import Registry
    from boukensha.prompt_builder import PromptBuilder
    from boukensha.client import Client

from boukensha.errors import ApiError


class Agent:
    """
    The agent loop - sends requests, dispatches tools, and knows when to stop.

    The Agent:
    1. Sends messages to the API
    2. Checks if stop_reason is "tool_use"
    3. If yes: extracts tool calls, dispatches them, injects results, loops
    4. If no: returns final text response
    5. Enforces max_iterations limit with graceful wind-down
    """

    # Default iteration ceiling
    MAX_ITERATIONS = 25

    # Wind-down call settings
    WRAP_UP_OUTPUT_TOKENS = 400
    WRAP_UP_DIRECTIVE = (
        "You have reached your action limit for this turn. Do not call any more tools. "
        "Briefly summarize what you accomplished, what is still unfinished, and the "
        "single next action you would take."
    )

    def __init__(
        self,
        context: Context,
        registry: Registry,
        builder: PromptBuilder,
        client: Client,
        task_settings: Optional[Dict[str, Any]] = None,
        max_iterations: Optional[int] = None,
        max_output_tokens: Optional[int] = None,
    ) -> None:
        self._context = context
        self._registry = registry
        self._builder = builder
        self._client = client
        self._max_iterations = self._resolve_max_iterations(task_settings, max_iterations)
        self._max_output_tokens = self._resolve_max_output_tokens(task_settings, max_output_tokens)
        self._iteration = 0

    def run(self) -> str:
        """
        Run the agent loop until completion.

        Returns:
            Final text response from the agent
        """
        while True:
            # Check iteration limit
            if self._iteration_limit_reached():
                return self._wrap_up("max_iterations")

            self._iteration += 1
            print(f"[iteration {self._iteration}/{self._max_iterations}]")

            # Make API call
            response = self._client.call(**self._call_opts())
            parsed = self._builder.parse_response(response)

            # Check stop reason
            if parsed["stop_reason"] == "tool_use":
                self._handle_tool_calls(parsed["content"])
            else:
                return self._extract_text(parsed["content"])

    def _handle_tool_calls(self, content: List[Dict[str, Any]]) -> None:
        """Handle tool use blocks by dispatching and injecting results."""
        # Add assistant message with tool use blocks
        self._context.add_message("assistant", content)

        # Dispatch each tool call
        for block in content:
            if block["type"] == "tool_use":
                name = block["name"]
                args = block["input"]
                use_id = block["id"]

                print(f"  tool call → {name}({args})")
                result = self._registry.dispatch(name, args)
                print(f"  tool result → {str(result)[:60]}")

                self._context.add_message("tool_result", str(result), tool_use_id=use_id)

    def _extract_text(self, content: List[Dict[str, Any]]) -> str:
        """Extract text from content blocks."""
        return "".join(block["text"] for block in content if block["type"] == "text")

    def _wrap_up(self, reason: str) -> str:
        """Make a final wind-down call without tools."""
        self._context.add_message("user", self.WRAP_UP_DIRECTIVE)

        try:
            response = self._client.call(tools=[], max_output_tokens=self.WRAP_UP_OUTPUT_TOKENS)
            text = self._extract_text(self._builder.parse_response(response)["content"])
            return text if text.strip() else self._fallback_message(reason)
        except ApiError:
            return self._fallback_message(reason)

    def _fallback_message(self, reason: str) -> str:
        """Return a fallback message when wind-down fails."""
        return (
            f"I reached my {self._max_iterations}-action limit for this turn before finishing "
            f"({reason}). Ask me to continue and I'll pick up from here."
        )

    def _iteration_limit_reached(self) -> bool:
        """Check if iteration limit has been reached."""
        return self._max_iterations > 0 and self._iteration >= self._max_iterations

    def _call_opts(self) -> Dict[str, Any]:
        """Get call options for API requests."""
        return {"max_output_tokens": self._max_output_tokens} if self._max_output_tokens else {}

    def _resolve_max_iterations(
        self, task_settings: Optional[Dict[str, Any]], explicit: Optional[int]
    ) -> int:
        """Resolve max_iterations from settings or explicit value."""
        if explicit is not None:
            return int(explicit)
        if task_settings and hasattr(self._context.task, 'max_iterations'):
            return self._context.task.max_iterations(task_settings)
        return self.MAX_ITERATIONS

    def _resolve_max_output_tokens(
        self, task_settings: Optional[Dict[str, Any]], explicit: Optional[int]
    ) -> Optional[int]:
        """Resolve max_output_tokens from settings or explicit value."""
        if explicit is not None:
            return explicit
        if task_settings and hasattr(self._context.task, 'max_output_tokens'):
            return self._context.task.max_output_tokens(task_settings)
        return None
```

### 2. Normalized Response Format

Every backend converts its response to this common shape:

```python
{
    "stop_reason": "tool_use" | "end_turn",
    "content": [
        {"type": "text", "text": "..."},
        {"type": "tool_use", "id": "...", "name": "...", "input": {...}}
    ]
}
```

**Backend-specific parsing:**

**Anthropic:**
```python
def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
    """Anthropic's content array is already in the normalized format."""
    stop_reason = "tool_use" if response["stop_reason"] == "tool_use" else "end_turn"
    return {
        "stop_reason": stop_reason,
        "content": response.get("content", [])
    }
```

**Ollama:**
```python
def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Ollama response to common format.
    Ollama doesn't assign call IDs - reuses function name as ID.
    """
    message = response.get("message", {})
    tool_calls = message.get("tool_calls", [])

    content = []

    # Add text if present
    if message.get("content"):
        content.append({"type": "text", "text": message["content"]})

    # Add tool calls
    for tc in tool_calls:
        fn = tc.get("function", {})
        content.append({
            "type": "tool_use",
            "id": fn.get("name"),  # Ollama uses name as ID
            "name": fn.get("name"),
            "input": fn.get("arguments", {})
        })

    return {
        "stop_reason": "tool_use" if tool_calls else "end_turn",
        "content": content
    }
```

### 3. Updated PromptBuilder

Add `parse_response` delegation:

```python
# Add to prompt_builder.py
def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse provider response into normalized format.

    Args:
        response: Raw API response

    Returns:
        Normalized response with stop_reason and content
    """
    return self._backend.parse_response(response)
```

### 4. Updated Client

Add `tools` parameter to override tool list:

```python
# Update client.py
def call(
    self, max_output_tokens: int = 1024, tools: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Make an API request.

    Args:
        max_output_tokens: Maximum tokens to generate
        tools: Optional tool list override (empty list disables tools)

    Returns:
        Parsed JSON response
    """
    # Pass tools to to_api_payload
    payload = self._builder.to_api_payload(
        max_output_tokens=max_output_tokens,
        tools=tools
    )
    # ... rest of implementation
```

### 5. Updated Base Backend

Add abstract `parse_response` method:

```python
# Add to backends/base.py
@abstractmethod
def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse provider response into normalized format.

    Args:
        response: Raw API response

    Returns:
        Dict with keys:
        - stop_reason: "tool_use" or "end_turn"
        - content: List of content blocks
    """
    ...
```

### 6. LoopError Exception

```python
# Add to errors.py
class LoopError(Exception):
    """
    Raised when the agent loop encounters an error.

    This error indicates something went wrong during the agent loop
    execution, such as malformed responses or unexpected states.
    """
    pass
```

### 7. Task Configuration Methods

Add to `tasks/base.py`:

```python
# Constants
DEFAULT_MAX_ITERATIONS = 25
DEFAULT_MAX_OUTPUT_TOKENS = 1024

@classmethod
def max_iterations(cls, settings: Dict[str, Any]) -> int:
    """Get max_iterations from settings."""
    return cls._integer_setting(settings, "max_iterations", DEFAULT_MAX_ITERATIONS)

@classmethod
def max_output_tokens(cls, settings: Dict[str, Any]) -> int:
    """Get max_output_tokens from settings."""
    return cls._integer_setting(settings, "max_output_tokens", DEFAULT_MAX_OUTPUT_TOKENS)

@classmethod
def _integer_setting(cls, settings: Dict[str, Any], key: str, default: int) -> int:
    """Fetch an integer setting with default."""
    value = cls._fetch(settings, key)
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
```

## Directory Structure

```
python/05_agent_loop/
├── boukensha/
│   ├── __init__.py              # Updated exports (v0.5.0)
│   ├── config.py                # From 04_api_client
│   ├── context.py               # From 04_api_client
│   ├── errors.py                # Updated: Added LoopError
│   ├── message.py               # From 04_api_client
│   ├── registry.py              # From 04_api_client
│   ├── tool.py                  # From 04_api_client
│   ├── prompt_builder.py        # Updated: Added parse_response
│   ├── client.py                # Updated: Added tools parameter
│   ├── agent.py                 # NEW: Agent loop implementation
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── base.py              # Updated: Added parse_response abstract method
│   │   ├── anthropic.py         # Updated: Added parse_response, system array format
│   │   ├── openai.py            # Updated: Added parse_response, assistant_message
│   │   ├── gemini.py            # Updated: Added parse_response, assistant_parts
│   │   ├── ollama.py            # Updated: Added parse_response, assistant_message
│   │   └── ollama_cloud.py      # Updated: Added parse_response, assistant_message
│   └── tasks/
│       ├── __init__.py
│       ├── base.py              # Updated: Added max_iterations, max_output_tokens
│       └── player.py
├── examples/
│   └── example.py               # NEW: Agent loop demonstration
├── prompts/
│   └── system.md                # Same as 04_api_client
├── requirements.txt             # Same dependencies
└── README.md                    # NEW: Documentation
```

## Implementation Phases

### Phase 1: Setup and Copy (30 min)

1. Copy from 04_api_client
2. Create directory structure

### Phase 2: Update Errors (15 min)

1. Add `LoopError` to errors.py
2. Update `__init__.py` exports

### Phase 3: Update Tasks Base (30 min)

1. Add `DEFAULT_MAX_ITERATIONS` and `DEFAULT_MAX_OUTPUT_TOKENS`
2. Implement `max_iterations` class method
3. Implement `max_output_tokens` class method
4. Implement `_integer_setting` helper

### Phase 4: Update Client (30 min)

1. Add `tools` parameter to `call` method
2. Pass `tools` to `to_api_payload`
3. Update type hints

### Phase 5: Update PromptBuilder (15 min)

1. Add `parse_response` method that delegates to backend
2. Update `to_api_payload` to accept `tools` parameter

### Phase 6: Update Backends (2-3 hours)

For **each** backend:

1. **Update `to_payload`** to accept `tools` parameter
2. **Implement `parse_response`** to normalize response
3. **Implement `assistant_message`** if needed (Ollama, OpenAI, Gemini, OllamaCloud)
4. **Fix Anthropic system format** to array (we already did this in Ruby)

**Anthropic:**
- System prompt in array format: `[{"type": "text", "text": "..."}]`
- `parse_response`: stop_reason + content (already normalized)
- No `assistant_message` needed

**OpenAI:**
- `parse_response`: Extract from `choices[0].message`
- `assistant_message`: Rebuild with `tool_calls` array

**Gemini:**
- `parse_response`: Convert `functionCall` parts
- `assistant_parts`: Rebuild parts array

**Ollama & OllamaCloud:**
- `parse_response`: Extract from `message`, use name as ID
- `assistant_message`: Rebuild with `tool_calls`

### Phase 7: Implement Agent (2 hours)

1. Create `agent.py`
2. Implement `__init__` with all parameters
3. Implement `run` loop
4. Implement `_handle_tool_calls`
5. Implement `_extract_text`
6. Implement `_wrap_up`
7. Implement helper methods

### Phase 8: Example and Testing (1 hour)

1. Create `example.py` demonstrating agent loop
2. Test with real API
3. Verify tool calling works
4. Check iteration limit and wind-down

### Phase 9: Documentation (30 min)

1. Create comprehensive README.md
2. Update `__init__.py` exports

## Key Python Patterns

### 1. Message Content as List or String

Context.add_message must handle both:

```python
# String content (simple messages)
ctx.add_message("user", "Hello")

# List content (assistant messages with tool use)
ctx.add_message("assistant", [
    {"type": "text", "text": "I'll help"},
    {"type": "tool_use", "id": "...", "name": "read_file", "input": {...}}
])
```

Update `context.py`:

```python
def add_message(
    self, role: str, content: Any, tool_use_id: Optional[str] = None
) -> None:
    """
    Add a message to the conversation history.

    Args:
        role: Message role (user, assistant, tool_result)
        content: Message content (string or list of content blocks)
        tool_use_id: Optional tool use ID for tool_result messages
    """
    # Store content as-is (can be string or list)
    self._messages.append(
        Message(role=role, content=content, tool_use_id=tool_use_id)  # type: ignore
    )
```

### 2. Backend assistant_message Pattern

```python
def _assistant_message(self, content: Any) -> Dict[str, Any]:
    """
    Rebuild provider-specific assistant message from normalized content.

    Args:
        content: String or list of content blocks

    Returns:
        Provider-specific message dict
    """
    # Normalize to list
    if isinstance(content, str):
        blocks = [{"type": "text", "text": content}]
    else:
        blocks = content

    # Extract text and tool blocks
    text_blocks = [b for b in blocks if b["type"] == "text"]
    tool_blocks = [b for b in blocks if b["type"] == "tool_use"]

    # Rebuild provider format
    message = {
        "role": "assistant",
        "content": "".join(b["text"] for b in text_blocks)
    }

    if tool_blocks:
        message["tool_calls"] = [
            {
                "function": {
                    "name": b["name"],
                    "arguments": b["input"]
                }
            }
            for b in tool_blocks
        ]

    return message
```

## Testing Strategy

### 1. Single Tool Call
```python
agent = Agent(context=ctx, registry=registry, builder=builder, client=client)
result = agent.run()
assert "README" in result  # Should call list_directory
```

### 2. Multiple Tool Calls
```python
# Agent should call list_directory, then read_file
result = agent.run()
assert "README" in result
assert "Boukensha" in result
```

### 3. Iteration Limit
```python
# Set max_iterations=2
agent = Agent(..., max_iterations=2)
result = agent.run()
# Should wind down after 2 iterations
assert "action limit" in result or result  # Either wrap-up or completion
```

### 4. Parse Response
```python
# Test each backend's parse_response
response = {...}  # Provider-specific response
parsed = backend.parse_response(response)
assert "stop_reason" in parsed
assert "content" in parsed
assert parsed["stop_reason"] in ["tool_use", "end_turn"]
```

## Expected Output

```
=== BOUKENSHA Step 5: Agent Loop ===

Config: #<Boukensha::Config dir=/Users/you/.boukensha tasks=player>
Provider: anthropic
Model: claude-haiku-4-5
Max iterations: 25
Max output tokens: 1024

[iteration 1/25]
  tool call → read_file({'path': 'README.md'})
  tool result → # Boukensha 05: Agent Loop...

[iteration 2/25]
  tool call → list_directory({'path': '.'})
  tool result → README.md, examples, lib, prompts

=== FINAL RESPONSE ===
I've read the README.md file. This is the Boukensha MUD player assistant framework,
step 5 which introduces the agent loop. The framework can make API calls to LLM
providers, dispatch tools, and run autonomously until completion.

The files in the current directory are: README.md, examples, lib, prompts.
```

## Validation Checklist

- [ ] Agent class implemented
- [ ] LoopError added to errors.py
- [ ] parse_response in all 5 backends
- [ ] assistant_message in Ollama, OpenAI, Gemini, OllamaCloud
- [ ] Anthropic system prompt in array format
- [ ] max_iterations and max_output_tokens in tasks/base.py
- [ ] Client accepts tools parameter
- [ ] PromptBuilder delegates parse_response
- [ ] Context handles string and list content
- [ ] Example demonstrates agent loop
- [ ] Iteration limit enforced with wind-down
- [ ] Tool calls dispatched correctly
- [ ] README comprehensive
- [ ] Type hints throughout
- [ ] Python 3.8+ compatible

## Timeline Estimate

- **Phase 1 (Setup):** 30 min
- **Phase 2 (Errors):** 15 min
- **Phase 3 (Tasks Base):** 30 min
- **Phase 4 (Client):** 30 min
- **Phase 5 (PromptBuilder):** 15 min
- **Phase 6 (Backends):** 2-3 hours
- **Phase 7 (Agent):** 2 hours
- **Phase 8 (Example/Testing):** 1 hour
- **Phase 9 (Documentation):** 30 min

**Total:** 6-8 hours

## Success Criteria

1. Agent loop runs successfully
2. Tools dispatched and results injected
3. Iteration limit enforced
4. Wind-down call works
5. All 5 backends parse responses correctly
6. Type hints pass mypy --strict
7. Example runs with real API
8. Final response returned correctly

## Notes

- **Normalized format is key**: All backends must convert to the same shape
- **assistant_message is the inverse**: Rebuilds provider format from normalized blocks
- **Tool call IDs vary**: Anthropic/OpenAI have IDs, Ollama/Gemini use names
- **System array format**: Must be implemented for Anthropic compatibility
- **Content can be string or list**: Context must handle both
- **No tool loop yet in 04_api_client**: This is the first step with the actual loop

## Architectural Insights

### Why This Pattern Matters

1. **Normalized Responses**: Agent doesn't know about provider differences
2. **Separation of Concerns**: Each backend handles its own format
3. **Graceful Termination**: Iteration limit prevents runaway loops
4. **Tool Result Ordering**: Assistant message must come before tool_result

### Design Quote from Ruby README

> "Every backend speaks the same normalized shape. Five providers means five different response formats... Rather than teach the Agent loop about each of these, every backend implements parse_response, converting its raw response into one common shape."

## Python 3.8 Compatibility

- Type hints use `typing.Dict`, `typing.Any`, `typing.List`, `typing.Optional`
- `from __future__ import annotations`
- No Python 3.9+ features

## What's Next

This step completes the core agent functionality. Future steps will:

1. **Step 6+:** Add MUD connectivity
2. **Step 7+:** Build complete autonomous agent with world interaction

For now, this is about **the agent loop** - calling the API, dispatching tools, and knowing when to stop.

## See Also

- Original Ruby implementation: `ruby/05_agent_loop/`
- Port plan document: `docs/plans/python_port/05_agent_loop` (this file)
- Previous step: `python/04_api_client/`
