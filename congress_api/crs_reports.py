"""Congressional Research Service (CRS) report endpoints for the Congress.gov API.

The API offers no keyword search or sorting for CRS reports, and caps each
request at 250 results. ``search()`` works around this by paging through the
listing and matching locally.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from .client import CongressClient

MAX_PAGE_SIZE = 250
DEEP_SEARCH_WORKERS = 8
_DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _to_api_datetime(value: str | None, end_of_day: bool = False) -> str | None:
    """Accept 'YYYY-MM-DD' or a full timestamp; return the API's 'YYYY-MM-DDTHH:MM:SSZ'."""
    if value is None:
        return None
    if _DATE_ONLY.match(value):
        return f"{value}T23:59:59Z" if end_of_day else f"{value}T00:00:00Z"
    return value


class CrsReports:
    """Methods for CRS report endpoints."""

    def __init__(self, client: CongressClient):
        self.client = client

    def _date_params(self, from_date: str | None, to_date: str | None) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if from_date:
            params["fromDateTime"] = _to_api_datetime(from_date)
        if to_date:
            params["toDateTime"] = _to_api_datetime(to_date, end_of_day=True)
        return params

    def list(
        self,
        limit: int = 20,
        offset: int = 0,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        """Return one page of CRS reports, newest first.

        ``limit`` is capped at 250 by the API. Use ``iter()`` for more.
        Dates filter on when a report was last updated ('YYYY-MM-DD' accepted).
        """
        params = {"limit": min(limit, MAX_PAGE_SIZE), "offset": offset}
        params.update(self._date_params(from_date, to_date))
        return self.client.get("crsreport", **params)

    def iter(
        self,
        max_items: int | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield CRS reports across as many pages as needed (250 per request)."""
        yield from self.client.paginate(
            "crsreport",
            key="CRSReports",
            limit=MAX_PAGE_SIZE,
            max_items=max_items,
            **self._date_params(from_date, to_date),
        )

    def get(self, report_id: str) -> dict[str, Any]:
        """Get one report (e.g. 'RS21534'): authors, summary, topics, PDF/HTML links."""
        data = self.client.get(f"crsreport/{report_id.upper()}")
        return data.get("CRSReport", data)

    def search(
        self,
        terms: str,
        from_date: str | None = None,
        to_date: str | None = None,
        content_type: str | None = None,
        deep: bool = False,
        max_results: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield reports whose title or ID contains every word in ``terms``.

        Matching is case-insensitive and anchored at word starts: 'Oman' matches
        'Omani' but not 'Romania' or 'Woman'.

        A full scan of all reports takes about 60 requests. Narrow it with
        ``from_date``/``to_date`` (last-updated dates).

        ``content_type`` filters on 'Reports', 'Resources' (In Focus briefs) or 'Posts'
        (Insights and Legal Sidebars).

        ``deep=True`` also searches each report's summary, topics and authors.
        That costs one extra request per report scanned (run 8 at a time), so pair it
        with a date range.
        Matches found this way are returned as full report details.
        """
        patterns = [re.compile(rf"\b{re.escape(w)}", re.IGNORECASE) for w in terms.split() if w]

        def matches(text: str) -> bool:
            return all(p.search(text) for p in patterns)

        def text_of(item: dict[str, Any], detail: dict[str, Any] | None = None) -> str:
            parts = [str(item.get("id", "")), str(item.get("title", ""))]
            if detail:
                parts.append(str(detail.get("summary") or ""))
                parts += [t.get("topic", "") for t in detail.get("topics") or []]
                parts += [a.get("author", "") for a in detail.get("authors") or []]
            return " ".join(parts)

        def results_in(batch: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
            if not deep:
                yield from (i for i in batch if matches(text_of(i)))
                return
            # Fetch details only for reports whose title didn't already match, in parallel.
            need = [i["id"] for i in batch if not matches(text_of(i))]
            with ThreadPoolExecutor(max_workers=DEEP_SEARCH_WORKERS) as pool:
                details = dict(zip(need, pool.map(self.get, need), strict=True))
            for item in batch:
                if item["id"] not in details:
                    yield item
                elif matches(text_of(item, details[item["id"]])):
                    yield details[item["id"]]

        found = 0
        batch: list[dict[str, Any]] = []
        items = self.iter(from_date=from_date, to_date=to_date)
        while True:
            item = next(items, None)
            if item is not None:
                if content_type and item.get("contentType", "").lower() != content_type.lower():
                    continue
                batch.append(item)
                if len(batch) < MAX_PAGE_SIZE:
                    continue
            for result in results_in(batch):
                yield result
                found += 1
                if max_results is not None and found >= max_results:
                    return
            batch = []
            if item is None:
                return
