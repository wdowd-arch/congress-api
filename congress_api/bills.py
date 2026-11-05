"""Bill endpoints for the Congress.gov API."""

from __future__ import annotations

from typing import Any

from .client import VALID_BILL_TYPES, CongressClient


class Bills:
    """Methods for bill-related endpoints."""

    def __init__(self, client: CongressClient):
        self.client = client

    def _validate_type(self, bill_type: str) -> str:
        bt = bill_type.lower()
        if bt not in VALID_BILL_TYPES:
            raise ValueError(
                f"Invalid bill_type '{bill_type}'. Must be one of: {', '.join(sorted(VALID_BILL_TYPES))}"
            )
        return bt

    def list(
        self,
        congress: int | None = None,
        bill_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        """List bills, optionally filtered by congress and/or bill type."""
        path = "bill"
        if congress is not None:
            path += f"/{congress}"
            if bill_type:
                path += f"/{self._validate_type(bill_type)}"
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if from_date:
            params["fromDateTime"] = f"{from_date}T00:00:00Z" if "T" not in from_date else from_date
        if to_date:
            params["toDateTime"] = f"{to_date}T00:00:00Z" if "T" not in to_date else to_date
        return self.client.get(path, **params)

    def get(self, congress: int, bill_type: str, number: int) -> dict[str, Any]:
        """Get details for a specific bill. Returns the inner 'bill' object."""
        path = f"bill/{congress}/{self._validate_type(bill_type)}/{number}"
        data = self.client.get(path)
        return data.get("bill", data)

    def _sub(
        self, sub: str, congress: int, bill_type: str, number: int, limit: int = 20, offset: int = 0
    ) -> dict[str, Any]:
        path = f"bill/{congress}/{self._validate_type(bill_type)}/{number}/{sub}"
        return self.client.get(path, limit=limit, offset=offset)

    def actions(self, congress: int, bill_type: str, number: int, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        return self._sub("actions", congress, bill_type, number, limit, offset)

    def cosponsors(self, congress: int, bill_type: str, number: int, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        return self._sub("cosponsors", congress, bill_type, number, limit, offset)

    def subjects(self, congress: int, bill_type: str, number: int, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        return self._sub("subjects", congress, bill_type, number, limit, offset)

    def summaries(self, congress: int, bill_type: str, number: int, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        return self._sub("summaries", congress, bill_type, number, limit, offset)

    def text(self, congress: int, bill_type: str, number: int, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        return self._sub("text", congress, bill_type, number, limit, offset)

    def titles(self, congress: int, bill_type: str, number: int, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        return self._sub("titles", congress, bill_type, number, limit, offset)

    def amendments(self, congress: int, bill_type: str, number: int, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        return self._sub("amendments", congress, bill_type, number, limit, offset)

    def committees(self, congress: int, bill_type: str, number: int, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        return self._sub("committees", congress, bill_type, number, limit, offset)

    def related_bills(self, congress: int, bill_type: str, number: int, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        return self._sub("relatedbills", congress, bill_type, number, limit, offset)
