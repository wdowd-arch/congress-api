"""Command-line interface for the Congress.gov API client."""

from __future__ import annotations

import json
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from congress_api import CongressClient
from congress_api.bills import Bills
from congress_api.crs_reports import CrsReports
from congress_api.exceptions import APIError
from congress_api.members import Members

app = typer.Typer(help="Congress.gov API v3 CLI", no_args_is_help=True)
bills_app = typer.Typer(help="Bill commands")
members_app = typer.Typer(help="Member commands")
crs_app = typer.Typer(help="Congressional Research Service report commands")
app.add_typer(bills_app, name="bills")
app.add_typer(members_app, name="members")
app.add_typer(crs_app, name="crs")

console = Console()


def _client() -> CongressClient:
    try:
        return CongressClient()
    except APIError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _handle(fn):
    """Decorator that catches APIError and exits cleanly. Preserves signature for Typer."""
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except APIError as e:
            console.print(f"[red]API Error ({e.status_code}):[/red] {e}")
            raise typer.Exit(1)

    return wrapper


def _table(items: list[dict[str, Any]], columns: list[str], title: str = "") -> None:
    if not items:
        console.print("[yellow]No results[/yellow]")
        return
    table = Table(title=title, show_header=True, header_style="bold magenta")
    for col in columns:
        table.add_column(col)
    for item in items:
        table.add_row(*[str(item.get(col, ""))[:60] for col in columns])
    console.print(table)


@bills_app.command("list")
@_handle
def bills_list(
    congress: int | None = typer.Option(None, "--congress", help="Congress number"),
    bill_type: str | None = typer.Option(None, "--type", help="Bill type (hr, s, ...)"),
    limit: int = typer.Option(20, "--limit"),
) -> None:
    """List bills."""
    client = _client()
    data = Bills(client).list(congress=congress, bill_type=bill_type, limit=limit)
    items = data.get("bills") or []
    _table(items, ["congress", "type", "number", "title"], "Bills")


@bills_app.command("get")
@_handle
def bills_get(
    congress: int,
    bill_type: str,
    number: int,
    as_json: bool = typer.Option(False, "--json", help="Print raw JSON"),
) -> None:
    """Get a specific bill."""
    client = _client()
    bill = Bills(client).get(congress, bill_type, number)
    if as_json:
        console.print_json(json.dumps(bill, default=str))
    else:
        title = bill.get("title") or bill.get("titles", [{}])[0].get("title", "Unknown")
        console.print(Panel(f"[bold]{title}[/bold]\nCongress {congress} {bill_type.upper()} {number}", title="Bill"))


@bills_app.command("actions")
@_handle
def bills_actions(
    congress: int,
    bill_type: str,
    number: int,
    limit: int = typer.Option(20, "--limit"),
) -> None:
    """List actions on a bill."""
    client = _client()
    data = Bills(client).actions(congress, bill_type, number, limit=limit)
    items = data.get("actions") or []
    _table(items, ["actionDate", "text"], "Actions")


@members_app.command("list")
@_handle
def members_list(
    congress: int | None = typer.Option(None, "--congress"),
    state: str | None = typer.Option(None, "--state", help="Two-letter state code"),
    current: bool = typer.Option(False, "--current", help="Only current members"),
    limit: int = typer.Option(20, "--limit"),
) -> None:
    """List members."""
    client = _client()
    data = Members(client).list(
        congress=congress, state=state, current=current if current else None, limit=limit
    )
    items = data.get("members") or []
    _table(items, ["bioguideId", "directOrderName", "state", "party"], "Members")


@members_app.command("get")
@_handle
def members_get(
    bioguide_id: str,
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Get a member by Bioguide ID."""
    client = _client()
    data = Members(client).get(bioguide_id)
    member = data.get("member", data)
    if as_json:
        console.print_json(json.dumps(member, default=str))
    else:
        name = member.get("directOrderName") or bioguide_id
        console.print(Panel(f"[bold]{name}[/bold]\n{bioguide_id}", title="Member"))


_CRS_COLUMNS = ["id", "contentType", "updateDate", "title"]


def _crs_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**i, "updateDate": str(i.get("updateDate", ""))[:10]} for i in items]


@crs_app.command("list")
@_handle
def crs_list(
    limit: int = typer.Option(20, "--limit", help="Total reports to show (fetched 250 per request)"),
    from_date: str | None = typer.Option(None, "--from", help="Updated on/after YYYY-MM-DD"),
    to_date: str | None = typer.Option(None, "--to", help="Updated on/before YYYY-MM-DD"),
    as_json: bool = typer.Option(False, "--json", help="Print raw JSON"),
) -> None:
    """List CRS reports, most recently updated first."""
    client = _client()
    items = list(CrsReports(client).iter(max_items=limit, from_date=from_date, to_date=to_date))
    if as_json:
        console.print_json(json.dumps(items, default=str))
    else:
        _table(_crs_rows(items), _CRS_COLUMNS, f"CRS reports ({len(items)})")


@crs_app.command("get")
@_handle
def crs_get(
    report_id: str,
    as_json: bool = typer.Option(False, "--json", help="Print raw JSON"),
) -> None:
    """Get one CRS report by ID (e.g. RS21534)."""
    client = _client()
    r = CrsReports(client).get(report_id)
    if as_json:
        console.print_json(json.dumps(r, default=str))
        return
    authors = ", ".join(a.get("author", "") for a in r.get("authors") or [])
    topics = ", ".join(t.get("topic", "") for t in r.get("topics") or [])
    links = "\n".join(f"{f.get('format')}: {f.get('url')}" for f in r.get("formats") or [])
    body = (
        f"[bold]{r.get('title', report_id)}[/bold]\n"
        f"{r.get('id', report_id)} · {r.get('contentType', '')} · {r.get('status', '')} · "
        f"version {r.get('currentVersion', r.get('version', ''))}\n"
        f"Published {str(r.get('publishDate', ''))[:10]} · updated {str(r.get('updateDate', ''))[:10]}\n"
        f"Authors: {authors or 'n/a'}\nTopics: {topics or 'n/a'}\n\n"
        f"{r.get('summary') or ''}\n\n{links}"
    )
    console.print(Panel(body, title="CRS report"))


@crs_app.command("search")
@_handle
def crs_search(
    terms: str,
    from_date: str | None = typer.Option(None, "--from", help="Updated on/after YYYY-MM-DD"),
    to_date: str | None = typer.Option(None, "--to", help="Updated on/before YYYY-MM-DD"),
    content_type: str | None = typer.Option(None, "--type", help="Reports, Resources or Posts"),
    deep: bool = typer.Option(
        False, "--deep", help="Also search summaries, topics and authors (1 request per report; use with --from)"
    ),
    limit: int | None = typer.Option(None, "--limit", help="Stop after this many matches"),
    as_json: bool = typer.Option(False, "--json", help="Print raw JSON"),
) -> None:
    """Search CRS report titles and IDs (every word must match)."""
    client = _client()
    with console.status("Searching CRS reports..."):
        items = list(
            CrsReports(client).search(
                terms, from_date=from_date, to_date=to_date, content_type=content_type,
                deep=deep, max_results=limit,
            )
        )
    if as_json:
        console.print_json(json.dumps(items, default=str))
    else:
        _table(_crs_rows(items), _CRS_COLUMNS, f"CRS reports matching '{terms}' ({len(items)})")


if __name__ == "__main__":
    app()
