# Boukensha 05: Agent Loop - Python Port

This is a Python port of the Boukensha `05_agent_loop` step, which introduces the **Agent Loop** - the heart of the framework.

## Overview

The Agent implements the core tool-use loop pattern:
1. Send messages to the API
2. Check if stop_reason is "tool_use"
3. If yes: extract tool calls, dispatch them, inject results, loop
4. If no: return final text response
5. Enforce max_iterations limit with graceful wind-down

## What's New in This Step

- **Agent**: The agent loop that orchestrates API calls and tool dispatch
- **Response Normalization**: All backends convert responses to a common format
- **Tool Calling**: Automatic dispatch of tool calls and result injection
- **Iteration Limiting**: MAX_ITERATIONS with graceful wind-down
- **LoopError**: Exception for agent loop errors

## Running the Example

```bash
./bin/python/05_agent_loop
```

Or directly:

```bash
cd python/05_agent_loop
python3 examples/example.py
```

## Requirements

- Python 3.8+
- PyYAML
- python-dotenv
- Valid API key (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)

## Architecture

The agent loop is provider-agnostic. Every backend normalizes its response to:

```python
{
    "stop_reason": "tool_use" | "end_turn",
    "content": [
        {"type": "text", "text": "..."},
        {"type": "tool_use", "id": "...", "name": "...", "input": {...}}
    ]
}
```

This allows the Agent to work with any provider without knowing the specifics of their API format.

## See Also

- Original Ruby implementation: `ruby/05_agent_loop/`
- Port plan: `docs/plans/python_port/05_agent_loop`
- Previous step: `python/04_api_client/`
