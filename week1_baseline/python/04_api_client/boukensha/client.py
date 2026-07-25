"""
HTTP client for LLM API requests with retry logic.

The Client handles POST requests to LLM provider APIs with automatic
retry on transient failures, exponential backoff, and error handling.
"""

from __future__ import annotations
import json
import time
import urllib.request
import urllib.error
from typing import TYPE_CHECKING, Dict, Any, Optional

if TYPE_CHECKING:
    from boukensha.prompt_builder import PromptBuilder

from boukensha.errors import ApiError


class Client:
    """
    HTTP client for LLM API requests with retry logic.

    The Client handles:
    - HTTP POST requests to provider APIs
    - Automatic retry on transient failures
    - Exponential backoff (0.5s, 1s, 2s)
    - SSL/TLS for HTTPS endpoints (automatic)
    - JSON response parsing

    Example:
        >>> from boukensha import PromptBuilder, Client
        >>> from boukensha.backends import Anthropic
        >>>
        >>> backend = Anthropic(api_key="sk-ant-...", model="claude-sonnet-4-6")
        >>> builder = PromptBuilder(context=ctx, backend=backend)
        >>> client = Client(builder)
        >>>
        >>> response = client.call(max_output_tokens=1024)
        >>> print(response["content"])
    """

    # HTTP status codes that should trigger a retry
    RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}

    # Maximum number of retry attempts
    MAX_RETRIES = 3

    # Base delay for exponential backoff (in seconds)
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

        This method will retry on transient failures (network errors,
        rate limiting, server errors) with exponential backoff.

        Args:
            max_output_tokens: Maximum tokens to generate (default: 1024)

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
                response_text = self._make_request(url, headers, payload)
                return json.loads(response_text)

            except urllib.error.HTTPError as e:
                # HTTP errors with status codes
                if e.code in self.RETRYABLE_STATUS_CODES and attempts < self.MAX_RETRIES:
                    time.sleep(self._retry_delay(attempts))
                    continue

                # Non-retryable HTTP error - raise immediately
                error_body = e.read().decode('utf-8') if e.fp else str(e)
                raise ApiError(
                    f"API request failed after {attempts} attempt{'s' if attempts > 1 else ''} "
                    f"({e.code}): {error_body}"
                ) from e

            except (urllib.error.URLError, OSError, TimeoutError) as e:
                # Transient network errors - retry if attempts remain
                last_error = e
                if attempts < self.MAX_RETRIES:
                    time.sleep(self._retry_delay(attempts))
                    continue

                # Exhausted all retries
                raise ApiError(
                    f"API request failed after {attempts} attempts: "
                    f"{e.__class__.__name__}: {e}"
                ) from e

        # Should not reach here, but just in case
        raise ApiError(
            f"API request failed after {attempts} attempts: {last_error}"
        )

    def _make_request(
        self, url: str, headers: Dict[str, str], payload: Dict[str, Any]
    ) -> str:
        """
        Make a single HTTP POST request.

        Args:
            url: API endpoint URL
            headers: HTTP headers dictionary
            payload: JSON payload dictionary

        Returns:
            Response body as string

        Raises:
            urllib.error.HTTPError: On HTTP error (4xx, 5xx)
            urllib.error.URLError: On connection error
            TimeoutError: On request timeout
        """
        # Encode payload as JSON bytes
        data = json.dumps(payload).encode('utf-8')

        # Create POST request
        request = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method='POST'
        )

        # Make request with 60 second timeout
        # SSL/TLS is handled automatically for https:// URLs
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read().decode('utf-8')

    def _retry_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay.

        The delay doubles with each attempt:
        - Attempt 1: 0.5s
        - Attempt 2: 1.0s
        - Attempt 3: 2.0s

        Args:
            attempt: Current attempt number (1-indexed)

        Returns:
            Delay in seconds
        """
        return self.BASE_RETRY_DELAY * (2 ** (attempt - 1))

    def __repr__(self) -> str:
        """Get a debug representation of the client."""
        backend_name = self._builder.backend.__class__.__name__
        model = self._builder.backend.model
        return f"#<Client backend={backend_name} model={model}>"
