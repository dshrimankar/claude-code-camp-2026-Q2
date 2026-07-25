# Port Plan: 04_api_client (Ruby → Python)

## Overview

This step introduces the **HTTP API Client** that takes the payload from `PromptBuilder` and sends it to the LLM provider's API endpoint. It's a single HTTP POST request with response parsing - no tool loop yet, just proving the round trip works.

**New Components:**
- `Client` - HTTP client with retry logic and error handling
- `ApiError` - Custom exception for API failures
- Updated `errors.py` with ApiError
- Example demonstrating real API calls

**Estimated Effort:** 3-4 hours
**New Lines of Code:** ~200 lines (Client + example + updates)

## What's New in This Step

### 1. Client Class (`lib/boukensha/client.rb`)

The Client handles HTTP communication with retry logic and error handling:

```ruby
# Ruby
module Boukensha
  class Client
    RETRYABLE_STATUS_CODES = [408, 409, 429, 500, 502, 503, 504].freeze
    TRANSIENT_ERRORS = [
      EOFError,
      Errno::ECONNRESET,
      Errno::ECONNREFUSED,
      Net::OpenTimeout,
      Net::ReadTimeout,
      OpenSSL::SSL::SSLError,
      SocketError,
      Timeout::Error
    ].freeze
    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 0.5

    def initialize(builder)
      @builder = builder
    end

    def call(max_output_tokens: 1024)
      uri          = URI(@builder.url)
      http         = Net::HTTP.new(uri.host, uri.port)
      http.use_ssl = uri.scheme == "https"
      http.verify_mode = OpenSSL::SSL::VERIFY_PEER

      request      = Net::HTTP::Post.new(uri, @builder.headers)
      request.body = @builder.to_api_payload(max_output_tokens: max_output_tokens).to_json

      attempts = 0
      response = nil

      loop do
        attempts += 1
        begin
          response = http.request(request)
        rescue *TRANSIENT_ERRORS => e
          raise ApiError, "..." if attempts > MAX_RETRIES
          sleep retry_delay(attempts)
          next
        end

        if retryable_response?(response) && attempts <= MAX_RETRIES
          sleep retry_delay(attempts)
          next
        end
        break
      end

      unless response.is_a?(Net::HTTPSuccess)
        raise ApiError, "API request failed after #{attempts} attempt(s) (#{response.code}): #{response.body}"
      end

      JSON.parse(response.body)
    end

    private

    def retryable_response?(response)
      RETRYABLE_STATUS_CODES.include?(response.code.to_i)
    end

    def retry_delay(attempt)
      BASE_RETRY_DELAY * (2**(attempt - 1))
    end
  end
end
```

**Python Translation:**
```python
# Python (boukensha/client.py)
import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from boukensha.errors import ApiError
from boukensha.prompt_builder import PromptBuilder


class Client:
    """
    HTTP client for LLM API requests with retry logic.

    The Client handles:
    - HTTP POST requests to provider APIs
    - Automatic retry on transient failures
    - Exponential backoff
    - SSL/TLS for HTTPS endpoints
    - JSON response parsing
    """

    RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}
    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 0.5

    def __init__(self, builder: PromptBuilder) -> None:
        """
        Initialize the client with a prompt builder.

        Args:
            builder: PromptBuilder instance with configured backend
        """
        self._builder = builder

    def call(self, max_output_tokens: int = 1024) -> Dict[str, Any]:
        """
        Make an API request and return the parsed JSON response.

        Args:
            max_output_tokens: Maximum tokens to generate

        Returns:
            Parsed JSON response as a dictionary

        Raises:
            ApiError: If the request fails after all retries
        """
        url = self._builder.url
        headers = self._builder.headers
        payload = self._builder.to_api_payload(max_output_tokens=max_output_tokens)

        attempts = 0
        last_error: Optional[Exception] = None

        while attempts < self.MAX_RETRIES:
            attempts += 1

            try:
                response = self._make_request(url, headers, payload)
                return json.loads(response)
            except urllib.error.HTTPError as e:
                # HTTP errors with status codes
                if e.code in self.RETRYABLE_STATUS_CODES and attempts < self.MAX_RETRIES:
                    time.sleep(self._retry_delay(attempts))
                    continue

                # Non-retryable HTTP error
                error_body = e.read().decode('utf-8') if e.fp else str(e)
                raise ApiError(
                    f"API request failed after {attempts} attempt{'s' if attempts > 1 else ''} "
                    f"({e.code}): {error_body}"
                ) from e

            except (urllib.error.URLError, OSError, TimeoutError) as e:
                # Transient network errors
                last_error = e
                if attempts < self.MAX_RETRIES:
                    time.sleep(self._retry_delay(attempts))
                    continue

                # Exhausted retries
                raise ApiError(
                    f"API request failed after {attempts} attempts: "
                    f"{e.__class__.__name__}: {e}"
                ) from e

        # Should not reach here, but just in case
        raise ApiError(
            f"API request failed after {attempts} attempts: {last_error}"
        )

    def _make_request(self, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> str:
        """
        Make a single HTTP POST request.

        Args:
            url: API endpoint URL
            headers: HTTP headers
            payload: JSON payload

        Returns:
            Response body as string

        Raises:
            urllib.error.HTTPError: On HTTP error
            urllib.error.URLError: On connection error
        """
        data = json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(url, data=data, headers=headers, method='POST')

        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read().decode('utf-8')

    def _retry_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay.

        Args:
            attempt: Current attempt number (1-indexed)

        Returns:
            Delay in seconds
        """
        return self.BASE_RETRY_DELAY * (2 ** (attempt - 1))
```

### 2. ApiError Exception (`boukensha/errors.py`)

Add ApiError to the existing errors module:

```python
# Update errors.py
class ApiError(Exception):
    """
    Raised when an API request fails.

    This error indicates the HTTP request to the LLM provider failed.
    Common causes:
    - Invalid API key (401 Unauthorized)
    - Rate limiting (429 Too Many Requests)
    - Server errors (500, 502, 503, 504)
    - Network connectivity issues
    - Malformed request payload (400 Bad Request)

    Example:
        >>> client.call()
        ApiError: API request failed after 3 attempts (429): Rate limit exceeded
    """
    pass
```

### 3. Updated System Prompt (`prompts/system.md`)

The system prompt for this step is more focused:

```markdown
You are Boukensha, an autonomous player exploring a CircleMUD world.

Use available tools to observe the world, act deliberately, and explain only what matters for the current turn.
```

## Directory Structure

```
python/04_api_client/
├── boukensha/
│   ├── __init__.py              # Updated exports
│   ├── config.py                # From 03_prompt_builder
│   ├── context.py               # From 03_prompt_builder
│   ├── errors.py                # Updated: Added ApiError
│   ├── message.py               # From 03_prompt_builder
│   ├── registry.py              # From 03_prompt_builder
│   ├── tool.py                  # From 03_prompt_builder
│   ├── prompt_builder.py        # From 03_prompt_builder
│   ├── client.py                # NEW: HTTP client
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
│   └── example.py               # NEW: Real API call demo
├── prompts/
│   └── system.md                # NEW: Updated system prompt
├── requirements.txt             # Same dependencies
└── README.md                    # NEW: Documentation
```

## Implementation Phases

### Phase 1: Setup and Copy (30 min)

1. **Copy from 03_prompt_builder:**
   - All files from `python/03_prompt_builder/boukensha/`
   - requirements.txt
   - Directory structure

2. **Create prompts directory:**
   ```bash
   mkdir -p prompts
   ```

### Phase 2: Implement Client (1-2 hours)

1. **Create client.py:**
   - `Client` class
   - Retry logic with exponential backoff
   - SSL/HTTPS handling (automatic with urllib)
   - Error handling for transient failures
   - JSON response parsing

2. **Key implementation details:**
   - Use `urllib.request` (standard library, no dependencies)
   - Handle retryable status codes: 408, 409, 429, 500, 502, 503, 504
   - Exponential backoff: 0.5s, 1s, 2s
   - Timeout of 60 seconds per request
   - Raise ApiError on failure

### Phase 3: Update Errors (15 min)

1. **Update errors.py:**
   - Add `ApiError` class with comprehensive docstring
   - Export in `__init__.py`

### Phase 4: Update System Prompt (15 min)

1. **Create prompts/system.md:**
   - Copy content from Ruby version
   - Focused on MUD exploration

### Phase 5: Create Example (1 hour)

1. **Create example.py:**
   - Setup config and context
   - Register `read_file` and `list_directory` tools
   - Create backend based on provider
   - Make real API call
   - Display response

2. **Example structure:**
   ```python
   # Setup
   config = Config()
   ctx = Context(...)
   registry = Registry(ctx)

   # Register tools
   def read_file(path: str) -> str:
       with open(path) as f:
           return f.read()

   registry.tool(name="read_file", ...)

   # Create client and call API
   backend = Anthropic(api_key=..., model=...)
   builder = PromptBuilder(context=ctx, backend=backend)
   client = Client(builder)

   response = client.call()
   print(json.dumps(response, indent=2))
   ```

### Phase 6: Documentation and Testing (30 min)

1. **Create README.md:**
   - Overview of HTTP client
   - Retry logic explanation
   - Example usage
   - Response format examples
   - Error handling guide

2. **Test the implementation:**
   - Run example with real API key
   - Verify retry logic (optional: mock failing requests)
   - Check response parsing

## Key Python Patterns

### 1. urllib.request for HTTP

```python
import urllib.request
import json

data = json.dumps(payload).encode('utf-8')
request = urllib.request.Request(url, data=data, headers=headers, method='POST')

with urllib.request.urlopen(request, timeout=60) as response:
    body = response.read().decode('utf-8')
    return json.loads(body)
```

### 2. Exception Handling for Retries

```python
try:
    response = self._make_request(url, headers, payload)
    return json.loads(response)
except urllib.error.HTTPError as e:
    if e.code in self.RETRYABLE_STATUS_CODES:
        time.sleep(self._retry_delay(attempts))
        # retry
except urllib.error.URLError as e:
    # Transient network error
    time.sleep(self._retry_delay(attempts))
    # retry
```

### 3. Exponential Backoff

```python
def _retry_delay(self, attempt: int) -> float:
    """Exponential backoff: 0.5s, 1s, 2s"""
    return self.BASE_RETRY_DELAY * (2 ** (attempt - 1))
```

## Testing Strategy

### 1. Success Case
```python
# Should return parsed JSON
client = Client(builder)
response = client.call(max_output_tokens=1024)
assert isinstance(response, dict)
assert "id" in response  # Anthropic
# or
assert "model" in response  # Ollama
```

### 2. Error Handling
```python
# Invalid API key should raise ApiError
backend = Anthropic(api_key="invalid", model="claude-sonnet-4-6")
builder = PromptBuilder(context=ctx, backend=backend)
client = Client(builder)

try:
    client.call()
    assert False, "Should have raised ApiError"
except ApiError as e:
    assert "401" in str(e) or "403" in str(e)
```

### 3. Retry Logic (Optional)
```python
# Mock failing requests to test retry
# This requires mocking urllib.request which is more complex
```

## Ruby vs Python Differences

### 1. HTTP Libraries

**Ruby:**
```ruby
require "net/http"

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
import urllib.request

data = json.dumps(payload).encode('utf-8')
request = urllib.request.Request(url, data=data, headers=headers, method='POST')

with urllib.request.urlopen(request, timeout=60) as response:
    body = response.read().decode('utf-8')
```

### 2. Exception Classes

**Ruby:**
```ruby
TRANSIENT_ERRORS = [
  EOFError,
  Errno::ECONNRESET,
  Net::OpenTimeout,
  # ...
].freeze

rescue *TRANSIENT_ERRORS => e
```

**Python:**
```python
# urllib raises fewer exception types
# urllib.error.URLError covers most transient failures

except (urllib.error.URLError, OSError, TimeoutError) as e:
```

### 3. SSL/TLS Handling

**Ruby:** Must configure explicitly
```ruby
http.use_ssl = uri.scheme == "https"
http.verify_mode = OpenSSL::SSL::VERIFY_PEER
```

**Python:** Automatic with urllib
```python
# SSL is handled automatically based on URL scheme
# No explicit configuration needed for https:// URLs
```

## Expected Output

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

## Response Format Examples

### Anthropic (Text Response)
```json
{
  "id": "msg_01XY",
  "type": "message",
  "role": "assistant",
  "content": [
    { "type": "text", "text": "Sure, let me read that file." }
  ],
  "stop_reason": "end_turn",
  "usage": { "input_tokens": 42, "output_tokens": 18 }
}
```

### Anthropic (Tool Use)
```json
{
  "id": "msg_01XY",
  "type": "message",
  "role": "assistant",
  "content": [
    { "type": "text", "text": "I'll list the directory." },
    {
      "type": "tool_use",
      "id": "toolu_01ABC",
      "name": "list_directory",
      "input": { "path": "." }
    }
  ],
  "stop_reason": "tool_use",
  "usage": { "input_tokens": 385, "output_tokens": 67 }
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

## Validation Checklist

- [ ] Client class implemented with retry logic
- [ ] ApiError added to errors.py
- [ ] Exponential backoff working (0.5s, 1s, 2s)
- [ ] SSL/HTTPS handled automatically
- [ ] Retryable status codes: 408, 409, 429, 500, 502, 503, 504
- [ ] Max 3 retries before raising ApiError
- [ ] JSON response parsing
- [ ] Example makes real API call
- [ ] System prompt updated
- [ ] README documents API client
- [ ] Comprehensive type hints
- [ ] Python 3.8+ compatible
- [ ] Exports updated in __init__.py

## Timeline Estimate

- **Phase 1 (Setup):** 30 min
- **Phase 2 (Client):** 1-2 hours
- **Phase 3 (Errors):** 15 min
- **Phase 4 (System Prompt):** 15 min
- **Phase 5 (Example):** 1 hour
- **Phase 6 (Documentation):** 30 min

**Total:** 3-4 hours

## Success Criteria

1. Client successfully makes HTTP requests
2. Retry logic works with exponential backoff
3. ApiError raised on failures
4. Example successfully calls real API
5. Response correctly parsed as JSON
6. Type hints pass mypy --strict
7. Works with all 5 providers (Anthropic, OpenAI, Gemini, Ollama, OllamaCloud)

## Notes

- **No external dependencies:** Uses `urllib.request` from standard library (equivalent to Ruby's `net/http`)
- **SSL automatic:** Python's urllib handles SSL/TLS automatically for https:// URLs
- **Simpler than Ruby:** Fewer exception types to handle, cleaner API
- **No tool loop yet:** This step just proves the round trip works - step 5 will add the agent loop
- **Real API calls:** The example actually calls the API (requires valid API key)
- **Response parsing:** Returns raw JSON - step 5 will parse tool use blocks

## Architectural Insights

### Why This Pattern Matters

1. **Separation of Concerns**: Client is separate from PromptBuilder
2. **Retry Resilience**: Handles transient failures gracefully
3. **Provider Agnostic**: Works with any backend's URL and headers
4. **Explicit Errors**: ApiError makes failures visible and debuggable
5. **Standard Library**: No dependencies = simpler deployment

### Design Notes from Ruby README

> "BOUKENSHA surfaces this explicitly rather than returning a confusing nil or partial response."

> "SSL is handled automatically. The client checks the URL scheme and enables SSL for https endpoints."

> "No gems, no bundle install. This is intentional — the HTTP call itself is trivial and should be visible, not hidden behind a library."

## Python 3.8 Compatibility

- `urllib.request` available in all Python 3.x versions
- Type hints use `typing.Dict`, `typing.Any`, `typing.Optional`
- `from __future__ import annotations` for forward references
- No Python 3.9+ features

## What's Next

This step proves the API round trip works. Future steps will:

1. **Step 5:** Parse tool use from responses and implement the agent loop
2. **Step 6:** Add MUD connectivity
3. **Step 7:** Build complete autonomous agent

For now, this is about **making the API call** - sending the payload and getting a response back.

## See Also

- Original Ruby implementation: `ruby/04_api_client/`
- Port plan document: `docs/plans/python_port/04_api_client` (this file)
- Previous step: `python/03_prompt_builder/`
