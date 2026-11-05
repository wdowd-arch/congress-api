"""Member endpoints for the Congress.gov API."""

from __future__ import annotations

from typing import Any

from .client import CongressClient


class Members:
    """Methods for member endpoints."""

    def __init__(self, client: CongressClient):
        self.client = client

    def list(
        self,
        congress: int | None = None,
        state: str | None = None,
        current: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List members, optionally filtered by congress, state, or current status."""
        if congress is not None and state:
            path = f"member/congress/{congress}/{state.upper()}"
        elif congress is not None:
            path = f"member/congress/{congress}"
        elif state:
            path = f"member/{state.upper()}"
        else:
            path = "member"
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if current is not None:
            params["currentMember"] = str(current).lower()
        return self.client.get(path, **params)

    def get(self, bioguide_id: str) -> dict[str, Any]:
        """Get details for a member by Bioguide ID."""
        return self.client.get(f"member/{bioguide_id}")

    def sponsored_legislation(
        self, bioguide_id: str, limit: int = 20, offset: int = 0, **params: Any
    ) -> dict[str, Any]:
        """Get legislation sponsored by a member."""
        return self.client.get(
            f"member/{bioguide_id}/sponsored-legislation", limit=limit, offset=offset, **params
        )

    def cosponsored_legislation(
        self, bioguide_id: str, limit: int = 20, offset: int = 0, **params: Any
    ) -> dict[str, Any]:
        """Get legislation cosponsored by a member."""
        return self.client.get(
            f"member/{bioguide_id}/cosponsored-legislation", limit=limit, offset=offset, **params
        )
