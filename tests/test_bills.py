"""Tests for Bills class."""

import httpx
import pytest
import respx

from congress_api import CongressClient
from congress_api.bills import Bills


@pytest.fixture
def bills(monkeypatch):
    monkeypatch.setenv("CONGRESS_API_KEY", "test-key")
    return Bills(CongressClient())


@respx.mock
def test_get_bill(bills):
    respx.get("https://api.congress.gov/v3/bill/118/hr/1").mock(
        return_value=httpx.Response(200, json={"bill": {"number": "1", "title": "Test"}})
    )
    data = bills.get(118, "hr", 1)
    assert data["number"] == "1"


@respx.mock
def test_invalid_bill_type(bills):
    with pytest.raises(ValueError, match="Invalid bill_type"):
        bills.get(118, "badtype", 1)


@respx.mock
def test_list_bills(bills):
    respx.get("https://api.congress.gov/v3/bill/118/hr").mock(
        return_value=httpx.Response(200, json={"bills": [{"number": "1"}]})
    )
    data = bills.list(congress=118, bill_type="hr")
    assert len(data["bills"]) == 1


@respx.mock
def test_actions(bills):
    respx.get("https://api.congress.gov/v3/bill/118/hr/1/actions").mock(
        return_value=httpx.Response(200, json={"actions": []})
    )
    data = bills.actions(118, "hr", 1)
    assert "actions" in data
