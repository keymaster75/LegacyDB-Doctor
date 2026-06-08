from typer.testing import CliRunner

from legacydb_doctor.cli import app

runner = CliRunner()


def test_drivers_command_runs():
    result = runner.invoke(app, ["drivers"])

    assert result.exit_code == 0
    assert "Installed ODBC drivers" in result.output


def test_scan_help_includes_fk_suggestions_option():
    result = runner.invoke(app, ["scan", "--help"])

    assert result.exit_code == 0
    assert "--fk-suggestions-out" in result.output


def test_scan_help_includes_summary_only_and_fk_suggestions_options():
    result = runner.invoke(app, ["scan", "--help"])

    assert result.exit_code == 0
    assert "--summary-only" in result.output
    assert "--fk-suggestions-out" in result.output

def test_scan_help_mentions_fk_suggestions_are_review_only_and_summary_compatible():
    result = runner.invoke(app, ["scan", "--help"])

    assert result.exit_code == 0
    assert "--fk-suggestions-out" in result.output
    assert "--summary-only" in result.output
    assert "review-only" in result.output
    assert "normal scan" in result.output

