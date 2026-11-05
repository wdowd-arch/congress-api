# Congress.gov API Python Client

Production-ready Python client library and CLI for the [Congress.gov API v3](https://api.congress.gov/).

## Installation

```bash
pip install -e .
# or
pip install congress-api
```

## API Key

Sign up for a free API key at <https://api.congress.gov/sign-up/>.

Set it as an environment variable:

```bash
export CONGRESS_API_KEY=your_key_here
```

Or create a `.env` file (see `.env.example`).

## Quick Start

```python
from congress_api import CongressClient
from congress_api.bills import Bills
from congress_api.members import Members

client = CongressClient()
bills = Bills(client)
members = Members(client)

# Get a specific bill (returns the inner bill object)
bill = bills.get(118, "hr", 1)
print(bill)

# List recent bills
recent = bills.list(congress=118, bill_type="hr", limit=10)
print(recent)

# List Massachusetts members
ma_members = members.list(state="MA")
print(ma_members)
```

### Async

```python
import asyncio
from congress_api import AsyncCongressClient

async def main():
    async with AsyncCongressClient() as client:
        data = await client.get("bill/118/hr/1")
        print(data)

asyncio.run(main())
```

## CLI

```bash
congress bills list --congress 118 --type hr --limit 5
congress bills get 118 hr 1
congress bills get 118 hr 1 --json
congress bills actions 118 hr 1 --limit 10
congress members list --state MA
congress members list --congress 118 --current
congress members get P000197
congress members get P000197 --json
```

Use `--json` to print raw JSON. Otherwise a readable table or panel is shown.

## Congressional Research Service reports

```bash
congress crs list --limit 20                     # most recently updated first
congress crs list --limit 1000                   # any size; fetched 250 per request
congress crs list --from 2026-10-01 --to 2026-10-31
congress crs get RS21534                         # authors, topics, summary, PDF/HTML links
congress crs search "oman"                       # title/ID search across all reports
congress crs search "tariff canada" --from 2026-01-01 --type Reports
congress crs search "tariff" --from 2026-10-01 --deep   # also searches summaries, topics, authors
```

The Congress.gov API has no keyword search for CRS reports and returns at most
250 per request, so `search` pages through the listing and matches locally:

- Every word must match, case-insensitive, at the start of a word ("oman" finds
  "Oman" and "Omani" but not "Romania").
- A title search of all ~14,000 reports takes about 60 requests (roughly 10 seconds).
- `--deep` fetches each report's details to search its summary, topics and
  authors. That's one request per report, so narrow it with `--from`/`--to`.
- `--from`/`--to` filter on the date a report was last updated, not first published.
- `--type` is `Reports`, `Resources` (In Focus briefs) or `Posts` (Insights, Legal Sidebars).

```python
from congress_api.crs_reports import CrsReports

crs = CrsReports(client)
crs.get("RS21534")
for r in crs.iter(max_items=1000, from_date="2026-10-01"):
    print(r["id"], r["title"])
hits = list(crs.search("tariff", from_date="2026-10-01", deep=True))
```

## Running Tests

```bash
pip install -e ".[dev]"
pytest -q
```

Tests mock all HTTP calls (via respx) and do not require a real API key.

## Features

- Sync and async clients built on httpx
- Automatic retries with exponential backoff on 429 and 5xx
- Pagination helper (`paginate`) that yields items until `pagination.next` is absent
- Custom exceptions (`AuthError`, `NotFoundError`, `RateLimitError`, `ServerError`, `APIError`)
- Type hints and docstrings
- Typer CLI with rich tables/panels
- Congressional Research Service reports: list, get and local keyword search
- Full test suite

## License

MIT
