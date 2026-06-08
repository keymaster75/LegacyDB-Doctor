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

