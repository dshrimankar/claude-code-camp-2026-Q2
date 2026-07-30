# Boukensha 06: The Logger - Python Port

This is a Python port of the Boukensha `06_the_logger` step, which adds **structured JSONL logging** to the framework.

## Overview

The Logger records all agent activities to session-based JSONL files:
- Iterations and limits
- Prompts sent to the API
- Tool calls and results
- Model responses with usage metrics
- Cost estimates in USD

## What's New in This Step

- **Logger**: Session-based JSONL logger for agent activities
- **Module-level state**: `debug()`, `quiet()`, `config()` functions
- **Cost tracking**: Automatic USD cost estimation for API calls
- **Session files**: Logs saved to `.boukensha/sessions/<session-id>.jsonl`
- **Usage normalization**: Consistent token counting across providers

## Running the Example

```bash
./bin/python/06_the_logger
```

Or directly:

```bash
cd python/06_the_logger
python3 examples/example.py
```

## Requirements

- Python 3.8+
- PyYAML
- python-dotenv
- Valid API key (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)

## Architecture

### Logger

The Logger writes structured JSON Lines (JSONL) to `.boukensha/sessions/<session-id>.jsonl`:

```python
from boukensha import Logger

# Create logger with optional session metadata
logger = Logger(
    snapshot={
        "provider": "anthropic",
        "model": "claude-sonnet-4-6",
        "task": "player"
    }
)

# Logger automatically records:
logger.iteration(n=1, max=25)
logger.prompt(messages=[...], tools={...})
logger.tool_call(name="read_file", args={...})
logger.tool_result(name="read_file", result="...", ok=True)
logger.response(text="...", usage={...}, task=..., backend=...)
logger.turn_end(reason="completed", iterations=5)

# Close when done
logger.close()
```

### Session ID Format

Sessions are identified by: `YYYYMMDDTHHMMSSZ-{8hex}`

Example: `20260125T143022Z-a1b2c3d4`

### Event Types

Each JSONL line contains one of these event types:

- `session_start`: Session initialization with metadata
- `iteration`: Iteration counter (n, max)
- `limit_reached`: When iteration limit is hit
- `prompt`: Messages and tools sent to API
- `tool_call`: Tool invocation (name, args)
- `tool_result`: Tool execution result (ok, error)
- `response`: Model response with usage and cost
- `turn_end`: Turn completion summary
- `raw`: Raw API response (debug mode only)

### Usage Normalization

The logger normalizes token counts across different providers:

| Provider | Input Key | Output Key |
|----------|-----------|------------|
| Anthropic | `input_tokens` | `output_tokens` |
| OpenAI | `prompt_tokens` | `completion_tokens` |
| Gemini | `promptTokenCount` | `candidatesTokenCount` |
| Ollama | `prompt_eval_count` | `eval_count` |

### Cost Estimation

The logger automatically estimates USD costs using backend pricing:

```python
# Example response event:
{
  "phase": "response",
  "text": "I've read the file...",
  "usage": {"input_tokens": 1234, "output_tokens": 567},
  "provider": "anthropic",
  "model": "claude-sonnet-4-6",
  "input_tokens": 1234,
  "output_tokens": 567,
  "cost_usd": 0.012195,  # Automatically calculated
  "session_id": "20260125T143022Z-a1b2c3d4",
  "at": "2026-01-25T14:30:23.456789"
}
```

## Module-Level Functions

```python
import boukensha

# Configuration
config = boukensha.config()  # Get global Config instance

# Debug mode
boukensha.debug()            # Enable debug logging
boukensha.is_debug()         # Check if debug enabled

# Quiet mode
boukensha.quiet()            # Suppress output
boukensha.loud()             # Enable output
boukensha.is_quiet()         # Check if quiet enabled
```

## Integration with Agent

The Agent automatically logs all activities:

```python
from boukensha import Agent, Logger

# Create logger (optional - Agent creates one if not provided)
logger = Logger()

# Pass to agent
agent = Agent(
    context=ctx,
    registry=registry,
    builder=builder,
    client=client,
    logger=logger  # Optional - defaults to Logger()
)

# Run agent - all activities are logged
result = agent.run()

# Close logger
logger.close()
```

## See Also

- Original Ruby implementation: `ruby/06_the_logger/`
- Port plan: `docs/plans/python_port/06_the_logger`
- Previous step: `python/05_agent_loop/`
