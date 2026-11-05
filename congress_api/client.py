"""Core HTTP client for the Congress.gov API v3.

Both synchronous and asynchronous clients are built on httpx.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .exceptions import APIError, AuthError, NotFoundError, RateLimitError, ServerError

load_dotenv()

BASE_URL = "https://api.congress.gov/v3"
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 5
VALID_BILL_TYPES = {"hr", "s", "hjres", "sjres", "hconres", "sconres", "hres", "sres"}


class _BaseClient:
    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key or os.getenv("CONGRESS_API_KEY")
        if not self.api_key:
            raise AuthError(
                "API key not found. Set the CONGRESS_API_KEY environment variable "
                "or pass api_key explicitly. Sign up at https://api.congress.gov/sign-up/"
            )
        self.timeout = timeout

    def _params(self, params: dict[str, Any] | None) -> dict[str, Any]:
        final = dict(params or {})
        final["api_key"] = self.api_key
        final.setdefault("format", "json")
        return final

    def _handle(self, status_code: int, data: Any) -> dict[str, Any]:
        if status_code in (401, 403):
            raise AuthError("Invalid or missing API key", status_code=status_code, response=data)
        if status_code == 404:
            raise NotFoundError("Resource not found", status_code=status_code, response=data)
        if status_code == 429:
            raise RateLimitError("Rate limit exceeded", status_code=status_code, response=data)
        if 500 <= status_code < 600:
            raise ServerError(f"Server error {status_code}", status_code=status_code, response=data)
        if status_code >= 400:
            raise APIError(f"API error {status_code}", status_code=status_code, response=data)
        return data if isinstance(data, dict) else {"data": data}


class CongressClient(_BaseClient):
    """Synchronous client using httpx."""

    def __init__(self, api_key: str | None = None, timeout: float = DEFAULT_TIMEOUT):
        super().__init__(api_key, timeout)
        self._client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> CongressClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    @retry(
        retry=retry_if_exception_type((RateLimitError, ServerError, httpx.RequestError, httpx.TimeoutException)),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        stop=stop_after_attempt(MAX_RETRIES),
        reraise=True,
    )
    def get(self, path: str, **params: Any) -> dict[str, Any]:
        """GET a path and return the JSON dict."""
        url = f"{BASE_URL}/{path.lstrip('/')}"
        try:
            resp = self._client.get(url, params=self._params(params))
            data = resp.json() if resp.content else {}
            return self._handle(resp.status_code, data)
        except httpx.RequestError as e:
            raise APIError(f"Request failed: {e}") from e

    def paginate(
        self,
        path: str,
        key: str,
        limit: int = 250,
        max_items: int | None = None,
        **params: Any,
    ) -> Iterator[dict[str, Any]]:
        """Yield items across pages using offset/limit. Stops when pagination.next is absent."""
        offset = 0
        yielded = 0
        while True:
            data = self.get(path, limit=limit, offset=offset, **params)
            items = data.get(key) or []
            if not isinstance(items, list):
                items = [items] if items else []
            for item in items:
                yield item
                yielded += 1
                if max_items is not None and yielded >= max_items:
                    return
            pagination = data.get("pagination") or {}
            if not pagination.get("next"):
                break
            offset += limit


class AsyncCongressClient(_BaseClient):
    """Asynchronous client using httpx."""

    def __init__(self, api_key: str | None = None, timeout: float = DEFAULT_TIMEOUT):
        super().__init__(api_key, timeout)
        self._client = httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncCongressClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()

    @retry(
        retry=retry_if_exception_type((RateLimitError, ServerError, httpx.RequestError, httpx.TimeoutException)),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        stop=stop_after_attempt(MAX_RETRIES),
        reraise=True,
    )
    async def get(self, path: str, **params: Any) -> dict[str, Any]:
        """Async GET a path and return the JSON dict."""
        url = f"{BASE_URL}/{path.lstrip('/')}"
        try:
            resp = await self._client.get(url, params=self._params(params))
            data = resp.json() if resp.content else {}
            return self._handle(resp.status_code, data)
        except httpx.RequestError as e:
            raise APIError(f"Request failed: {e}") from e

    async def paginate(
        self,
        path: str,
        key: str,
        limit: int = 250,
        max_items: int | None = None,
        **params: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """Async generator that yields items across pages."""
        offset = 0
        yielded = 0
        while True:
            data = await self.get(path, limit=limit, offset=offset, **params)
            items = data.get(key) or []
            if not isinstance(items, list):
                items = [items] if items else []
            for item in items:
                yield item
                yielded += 1
                if max_items is not None and yielded >= max_items:
                    return
            pagination = data.get("pagination") or {}
            if not pagination.get("next"):
                break
            offset += limit
