# Boukensha 04: API Client - Python Port

This is a Python port of the Boukensha `04_api_client` step, which introduces the **HTTP API Client** that makes real requests to LLM provider APIs.

## Overview

This step builds on `03_prompt_builder` by adding an HTTP client that takes the payload from `PromptBuilder` and sends it to the API endpoint. It's a single HTTP POST request with response parsing - no tool loop yet, just proving the round trip works.

**New Components:**
- **Client**: HTTP client with retry logic and exponential backoff
- **ApiError**: Custom exception raised when API requests fail
- Updated system prompt focused on MUD exploration

## Requirements

- Python 3.8+
- PyYAML
- python-dotenv
- Valid API key for your chosen provider (Anthropic, OpenAI, Gemini, Ollama, OllamaCloud)

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
python/04_api_client/
├── boukensha/
│   ├── __init__.py              # Updated exports (v0.4.0)
│   ├── config.py                # Configuration system
│   ├── context.py               # Context state manager
│   ├── errors.py                # Custom exceptions (added ApiError)
│   ├── message.py               # Message data structure
│   ├── registry.py              # Tool registry and dispatcher
│   ├── tool.py                  # Tool data structure
│   ├── prompt_builder.py        # Prompt builder facade
│   ├── client.py                # NEW: HTTP client with retry logic
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── anthropic.py
│   │   ├── openai.py
│   │   ├── gemini.py
│   │   ├── ollama.py
│   │   └── ollama_cloud.py
│   └── tasks/
│       ├── __init__.py
│       ├── base.py
│       └── player.py
├── examples/
│   └── example.py               # Real API call demonstration
├── prompts/
│   └── system.md                # Updated system prompt
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## What's New in This Step

### 1. Client Class (`boukensha/client.py`)

The Client handles HTTP communication with automatic retry logic:

```python
from boukensha import Client
from boukensha.prompt_builder import PromptBuilder
from boukensha.backends import Anthropic

# Setup backend and builder
backend = Anthropic(api_key="sk-ant-...", model="claude-sonnet-4-6")
builder = PromptBuilder(context=ctx, backend=backend)

# Create client and make request
client = Client(builder)
response = client.call(max_output_tokens=1024)

print(response)  # Parsed JSON response
```

**Features:**
- Automatic retry on transient failures
- Exponential backoff (0.5s, 1s, 2s)
- Retryable status codes: 408, 409, 429, 500, 502, 503, 504
- Maximum 3 retry attempts
- 60 second timeout per request
- SSL/TLS automatic for HTTPS endpoints
- Comprehensive error messages

### 2. Retry Logic

The Client automatically retries on:

**Retryable HTTP Status Codes:**
- 408 Request Timeout
- 409 Conflict
- 429 Too Many Requests (rate limiting)
- 500 Internal Server Error
- 502 Bad Gateway
- 503 Service Unavailable
- 504 Gateway Timeout

**Transient Network Errors:**
- Connection refused
- Connection reset
- Timeout errors
- DNS resolution failures
- SSL errors

**Exponential Backoff:**
- Attempt 1: No delay
- Attempt 2: 0.5 second delay
- Attempt 3: 1 second delay
- After 3 attempts: Raise `ApiError`

### 3. ApiError Exception

Raised when an API request fails after all retries:

```python
from boukensha.errors import ApiError

try:
    response = client.call()
except ApiError as e:
    print(f"API request failed: {e}")
    # ApiError: API request failed after 3 attempts (429): Rate limit exceeded
```

### 4. Updated System Prompt

The system prompt is now focused on MUD exploration:

```
You are Boukensha, an autonomous player exploring a CircleMUD world.

Use available tools to observe the world, act deliberately, and explain only what matters for the current turn.
```

## Running the Example

From the repository root:

```bash
./bin/python/04_api_client
```

Or directly:

```bash
cd python/04_api_client
python3 examples/example.py
```

### Setting API Keys

The example requires a valid API key. Set it as an environment variable:

**Anthropic (Claude):**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

**OpenAI (GPT):**
```bash
export OPENAI_API_KEY="sk-..."
```

**Google (Gemini):**
```bash
export GEMINI_API_KEY="..."
```

**Ollama Cloud:**
```bash
export OLLAMA_API_KEY="..."
```

**Local Ollama:**
No API key needed. Make sure Ollama is running on `http://localhost:11434`.

### Expected Output

```
=== BOUKENSHA Step 4: API Client ===

Config: #<Boukensha::Config dir=/Users/you/.boukensha tasks=player>
Provider: anthropic
Model: claude-haiku-4-5
Sending request to https://api.anthropic.com/v1/messages...

Raw response:
{
  "id": "msg_01XY...",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I'll use the list_directory tool to see what files are in the current directory."
    },
    {
      "type": "tool_use",
      "id": "toolu_01ABC...",
      "name": "list_directory",
      "input": {
        "path": "."
      }
    }
  ],
  "stop_reason": "tool_use",
  "usage": {
    "input_tokens": 385,
    "output_tokens": 67
  }
}
```

## Usage Examples

### Basic Usage

```python
from boukensha import Config, Context, Registry, Player, Client
from boukensha.prompt_builder import PromptBuilder
from boukensha.backends import Anthropic
import os

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
def read_file(path: str) -> str:
    with open(path) as f:
        return f.read()

registry.tool(
    name="read_file",
    description="Read a file",
    parameters={"path": {"type": "string"}},
    block=read_file
)

# Add user message
ctx.add_message("user", "What files are here?")

# Make API call
backend = Anthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    model="claude-haiku-4-5"
)
builder = PromptBuilder(context=ctx, backend=backend)
client = Client(builder)

response = client.call()
print(response)
```

### Error Handling

```python
from boukensha.errors import ApiError

try:
    response = client.call(max_output_tokens=1024)
    print("Success:", response)
except ApiError as e:
    if "401" in str(e) or "403" in str(e):
        print("Authentication error: Check your API key")
    elif "429" in str(e):
        print("Rate limit exceeded: Wait and try again")
    elif "500" in str(e):
        print("Server error: Try again later")
    else:
        print(f"API error: {e}")
```

### Using Different Providers

```python
from boukensha.backends import OpenAI, Gemini, Ollama

# OpenAI
backend = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    model="gpt-5.4"
)

# Gemini
backend = Gemini(
    api_key=os.environ["GEMINI_API_KEY"],
    model="gemini-2.5-flash"
)

# Local Ollama
backend = Ollama(model="gemma4:12b")

# Build and call
builder = PromptBuilder(context=ctx, backend=backend)
client = Client(builder)
response = client.call()
```

## API Reference

### Client

**Constructor:**
```python
Client(builder: PromptBuilder)
```

**Methods:**

#### `call(max_output_tokens: int = 1024) -> Dict[str, Any]`

Make an API request and return the parsed JSON response.

**Args:**
- `max_output_tokens` (int): Maximum tokens to generate (default: 1024)

**Returns:**
- `Dict[str, Any]`: Parsed JSON response

**Raises:**
- `ApiError`: If the request fails after all retries

**Example:**
```python
client = Client(builder)
response = client.call(max_output_tokens=2048)
```

### ApiError

Custom exception raised when API requests fail.

**Attributes:**
- Inherits from `Exception`
- Message includes status code and error details

**Example:**
```python
try:
    response = client.call()
except ApiError as e:
    print(f"Request failed: {e}")
```

## Response Format Examples

### Anthropic (Text Response)

```json
{
  "id": "msg_01XY",
  "type": "message",
  "role": "assistant",
  "content": [
    {"type": "text", "text": "Sure, let me read that file."}
  ],
  "stop_reason": "end_turn",
  "usage": {"input_tokens": 42, "output_tokens": 18}
}
```

### Anthropic (Tool Use)

```json
{
  "id": "msg_01XY",
  "type": "message",
  "role": "assistant",
  "content": [
    {"type": "text", "text": "I'll list the directory."},
    {
      "type": "tool_use",
      "id": "toolu_01ABC",
      "name": "list_directory",
      "input": {"path": "."}
    }
  ],
  "stop_reason": "tool_use",
  "usage": {"input_tokens": 385, "output_tokens": 67}
}
```

### Ollama

```json
{
  "model": "llama3.2",
  "message": {
    "role": "assistant",
    "content": "Sure, let me read that file."
  },
  "done_reason": "stop",
  "done": true
}
```

## Type Hints

This port uses comprehensive type hints throughout:

```python
from typing import Dict, Any
from boukensha import Client
from boukensha.prompt_builder import PromptBuilder

def make_request(builder: PromptBuilder) -> Dict[str, Any]:
    client = Client(builder)
    return client.call(max_output_tokens=1024)
```

### Type Checking

Optional but recommended:

```bash
pip install mypy
mypy boukensha/ --strict
```

## Differences from Ruby Version

### Python Advantages

1. **Simpler HTTP Library:**
   - Ruby: `net/http` requires verbose setup
   - Python: `urllib.request` is more concise

2. **Automatic SSL:**
   - Ruby: Must configure `use_ssl` and `verify_mode`
   - Python: SSL automatic for https:// URLs

3. **Cleaner Exception Handling:**
   - Ruby: Many specific exception types
   - Python: Fewer, more general exceptions

### Implementation Equivalence

- ✅ HTTP POST requests
- ✅ Retry logic with exponential backoff
- ✅ Retryable status codes
- ✅ Max 3 retries
- ✅ JSON response parsing
- ✅ ApiError on failure
- ✅ All functionality preserved

### Code Comparison

**Ruby:**
```ruby
uri = URI(url)
http = Net::HTTP.new(uri.host, uri.port)
http.use_ssl = true
http.verify_mode = OpenSSL::SSL::VERIFY_PEER

request = Net::HTTP::Post.new(uri, headers)
request.body = payload.to_json

response = http.request(request)
```

**Python:**
```python
data = json.dumps(payload).encode('utf-8')
request = urllib.request.Request(url, data=data, headers=headers, method='POST')

with urllib.request.urlopen(request, timeout=60) as response:
    body = response.read().decode('utf-8')
```

## No External Dependencies

The Client uses Python's standard library `urllib.request` (equivalent to Ruby's `net/http`). No external HTTP libraries needed - keeping the implementation simple and visible.

## Architectural Insights

### Why This Pattern Matters

1. **Separation of Concerns**: Client is separate from PromptBuilder
2. **Retry Resilience**: Handles transient failures gracefully
3. **Provider Agnostic**: Works with any backend's URL and headers
4. **Explicit Errors**: ApiError makes failures visible and debuggable
5. **Standard Library**: No dependencies = simpler deployment

### Design Quote from Ruby README

> "No gems, no bundle install. This is intentional — the HTTP call itself is trivial and should be visible, not hidden behind a library."

## What This Step Proves

This step demonstrates the complete round trip:

```
Context → PromptBuilder → Client → API → JSON Response
```

**What it does:**
- ✅ Serializes context to provider format
- ✅ Makes HTTP POST request
- ✅ Handles errors and retries
- ✅ Parses JSON response

**What it doesn't do yet:**
- ❌ Parse tool use from response
- ❌ Execute tools
- ❌ Loop until completion
- ❌ Connect to MUD server

Those features come in later steps.

## Python 3.8 Compatibility

- `urllib.request` available in all Python 3.x
- Type hints use `typing.Dict`, `typing.Any`, `typing.Optional`
- `from __future__ import annotations` for forward references
- No Python 3.9+ features

## Troubleshooting

### "ApiError: API request failed (401)"
Your API key is invalid or expired. Check your environment variable.

### "ApiError: API request failed (429)"
Rate limit exceeded. Wait a moment and try again.

### "ApiError: API request failed after 3 attempts"
Network connectivity issue or server is down. Check your internet connection.

### "Error: ANTHROPIC_API_KEY environment variable not set"
Set your API key:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

## What's Next

This step proves the API round trip works. Future steps will:

1. **Step 5:** Parse tool use from responses and implement the agent loop
2. **Step 6:** Add MUD connectivity
3. **Step 7:** Build complete autonomous agent

For now, this is about **making the API call** - sending the payload and getting a response back.

## See Also

- Original Ruby implementation: `ruby/04_api_client/`
- Port plan: `docs/plans/python_port/04_api_client`
- Previous step: `python/03_prompt_builder/`
