"""Tests for CrsReports class."""

import httpx
import respx

from congress_api import CongressClient
from congress_api.crs_reports import CrsReports

URL = "https://api.congress.gov/v3/crsreport"

LISTING = [
    {"id": "RS21534", "contentType": "Reports", "title": "Oman: Politics, Security, and U.S. Policy"},
    {"id": "R48440", "contentType": "Reports", "title": "Romania: Background and U.S. Relations"},
    {"id": "IN12568", "contentType": "Posts", "title": "Golden Dome: Strategic Stability"},
    {"id": "IF10447", "contentType": "Resources", "title": "U.S.-Brazil Trade Relations"},
]


def _mock_listing():
    return respx.get(URL).mock(
        return_value=httpx.Response(200, json={"CRSReports": LISTING, "pagination": {"count": 4}})
    )


def test_get_unwraps_and_uppercases_id():
    with respx.mock:
        route = respx.get(f"{URL}/RS21534").mock(
            return_value=httpx.Response(200, json={"CRSReport": {"id": "RS21534", "title": "Oman"}})
        )
        report = CrsReports(CongressClient()).get("rs21534")
        assert route.called
        assert report == {"id": "RS21534", "title": "Oman"}


def test_list_caps_limit_and_converts_dates():
    with respx.mock:
        route = respx.get(URL).mock(return_value=httpx.Response(200, json={"CRSReports": []}))
        CrsReports(CongressClient()).list(limit=1000, from_date="2026-01-01", to_date="2026-01-31")
        params = route.calls.last.request.url.params
        assert params["limit"] == "250"
        assert params["fromDateTime"] == "2026-01-01T00:00:00Z"
        assert params["toDateTime"] == "2026-01-31T23:59:59Z"


def test_iter_pages_past_250():
    page = [{"id": f"R{i}"} for i in range(250)]
    with respx.mock:
        route = respx.get(URL).mock(
            side_effect=[
                httpx.Response(200, json={"CRSReports": page, "pagination": {"next": "x"}}),
                httpx.Response(200, json={"CRSReports": page, "pagination": {"next": "x"}}),
            ]
        )
        items = list(CrsReports(CongressClient()).iter(max_items=300))
        assert len(items) == 300
        assert route.calls[1].request.url.params["offset"] == "250"


def test_search_matches_word_starts_only():
    with respx.mock:
        _mock_listing()
        ids = [r["id"] for r in CrsReports(CongressClient()).search("oman")]
        assert ids == ["RS21534"]  # not Romania


def test_search_requires_every_word_and_matches_ids():
    with respx.mock:
        _mock_listing()
        crs = CrsReports(CongressClient())
        assert [r["id"] for r in crs.search("brazil trade")] == ["IF10447"]
        assert [r["id"] for r in crs.search("brazil security")] == []
        assert [r["id"] for r in crs.search("in12568")] == ["IN12568"]


def test_search_content_type_filter():
    with respx.mock:
        _mock_listing()
        ids = [r["id"] for r in CrsReports(CongressClient()).search("u.s", content_type="posts")]
        assert ids == []
        ids = [r["id"] for r in CrsReports(CongressClient()).search("u.s", content_type="resources")]
        assert ids == ["IF10447"]


def test_deep_search_checks_summary_topics_authors():
    def detail(request):
        rid = request.url.path.rsplit("/", 1)[-1]
        summaries = {"IN12568": "Missile defense and tariffs on components."}
        return httpx.Response(
            200,
            json={"CRSReport": {"id": rid, "summary": summaries.get(rid, ""), "topics": [], "authors": []}},
        )

    with respx.mock:
        _mock_listing()
        detail_route = respx.get(url__regex=rf"{URL}/\w+").mock(side_effect=detail)
        crs = CrsReports(CongressClient())
        assert [r["id"] for r in crs.search("tariff")] == []
        assert not detail_route.called
        results = list(crs.search("tariff", deep=True))
        assert [r["id"] for r in results] == ["IN12568"]
        assert "summary" in results[0]  # deep matches come back as full details


def test_search_max_results():
    with respx.mock:
        _mock_listing()
        assert len(list(CrsReports(CongressClient()).search("u.s", max_results=1))) == 1
