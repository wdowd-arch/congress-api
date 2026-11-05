"""Custom exceptions for the Congress.gov API client."""

from typing import Any


class APIError(Exception):
    """Base exception for all API-related errors."""

    def __init__(self, message: str, status_code: int | None = None, response: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthError(APIError):
    """Raised when authentication fails (invalid or missing API key)."""


class NotFoundError(APIError):
    """Raised when a requested resource is not found (HTTP 404)."""


class RateLimitError(APIError):
    """Raised when the rate limit is exceeded (HTTP 429)."""


class ServerError(APIError):
    """Raised for 5xx server errors."""
