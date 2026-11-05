"""Congress.gov API v3 Python client and CLI.

A production-ready wrapper around the official Congress.gov API.
"""

from .client import AsyncCongressClient, CongressClient
from .exceptions import APIError, AuthError, NotFoundError, RateLimitError, ServerError

__version__ = "1.0.0"
__all__ = [
    "CongressClient",
    "AsyncCongressClient",
    "APIError",
    "AuthError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
]
