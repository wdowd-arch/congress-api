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
from congress_api.exceptions import APIError
from congress_api.members import Members

app = typer.Typer(help="Congress.gov API v3 CLI", no_args_is_help=True)
bills_app = typer.Typer(help="Bill commands")
members_app = typer.Typer(help="Member commands")
app.add_typer(bills_app, name="bills")
app.add_typer(members_app, name="members")

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


if __name__ == "__main__":
    app()
