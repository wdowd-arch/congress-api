"""Test configuration."""

import pytest


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("CONGRESS_API_KEY", "test-key-for-tests")
