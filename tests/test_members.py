"""Tests for Members class."""

import httpx
import respx

from congress_api import CongressClient
from congress_api.members import Members


def test_get_member(monkeypatch):
    monkeypatch.setenv("CONGRESS_API_KEY", "test-key")
    members = Members(CongressClient())
    with respx.mock:
        respx.get("https://api.congress.gov/v3/member/P000197").mock(
            return_value=httpx.Response(200, json={"member": {"bioguideId": "P000197"}})
        )
        data = members.get("P000197")
        assert data["member"]["bioguideId"] == "P000197"


def test_list_by_state(monkeypatch):
    monkeypatch.setenv("CONGRESS_API_KEY", "test-key")
    members = Members(CongressClient())
    with respx.mock:
        respx.get("https://api.congress.gov/v3/member/MA").mock(
            return_value=httpx.Response(200, json={"members": []})
        )
        data = members.list(state="MA")
        assert "members" in data
