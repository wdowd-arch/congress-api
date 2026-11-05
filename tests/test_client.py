"""Tests for the core client."""

import httpx
import pytest
import respx

from congress_api import CongressClient
from congress_api.exceptions import AuthError, NotFoundError, RateLimitError, ServerError


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("CONGRESS_API_KEY", raising=False)
    with pytest.raises(AuthError, match="API key not found"):
        CongressClient()


@respx.mock
def test_get_success(monkeypatch):
    monkeypatch.setenv("CONGRESS_API_KEY", "test-key")
    respx.get("https://api.congress.gov/v3/congress/current").mock(
        return_value=httpx.Response(200, json={"congress": {"number": 118}})
    )
    with CongressClient() as client:
        data = client.get("congress/current")
    assert data["congress"]["number"] == 118


@respx.mock
def test_not_found(monkeypatch):
    monkeypatch.setenv("CONGRESS_API_KEY", "test-key")
    respx.get("https://api.congress.gov/v3/bill/999/hr/1").mock(
        return_value=httpx.Response(404, json={"error": "not found"})
    )
    with CongressClient() as client:
        with pytest.raises(NotFoundError):
            client.get("bill/999/hr/1")


@respx.mock
def test_rate_limit(monkeypatch):
    monkeypatch.setenv("CONGRESS_API_KEY", "test-key")
    respx.get("https://api.congress.gov/v3/bill").mock(return_value=httpx.Response(429))
    with CongressClient() as client:
        with pytest.raises(RateLimitError):
            client.get("bill")


@respx.mock
def test_server_error(monkeypatch):
    monkeypatch.setenv("CONGRESS_API_KEY", "test-key")
    respx.get("https://api.congress.gov/v3/bill").mock(return_value=httpx.Response(500))
    with CongressClient() as client:
        with pytest.raises(ServerError):
            client.get("bill")


@respx.mock
def test_pagination(monkeypatch):
    monkeypatch.setenv("CONGRESS_API_KEY", "test-key")
    page1 = {
        "bills": [{"number": "1"}, {"number": "2"}],
        "pagination": {"next": "https://api.congress.gov/v3/bill?offset=2"},
    }
    page2 = {"bills": [{"number": "3"}], "pagination": {}}
    respx.get("https://api.congress.gov/v3/bill").mock(
        side_effect=[httpx.Response(200, json=page1), httpx.Response(200, json=page2)]
    )
    with CongressClient() as client:
        items = list(client.paginate("bill", key="bills", limit=2))
    assert [i["number"] for i in items] == ["1", "2", "3"]
