"""CLI tests."""

from typer.testing import CliRunner

from congress_api.cli import app

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "bills" in result.stdout
    assert "members" in result.stdout


def test_bills_help():
    result = runner.invoke(app, ["bills", "--help"])
    assert result.exit_code == 0
    assert "list" in result.stdout
    assert "get" in result.stdout
