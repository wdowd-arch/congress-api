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

client = CongressClient()
bills = Bills(client)

bill = bills.get(118, "hr", 1)
print(bill)
```

See full docs in the repository.
