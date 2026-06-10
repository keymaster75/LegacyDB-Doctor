from typer.testing import CliRunner

from legacydb_doctor.cli import app, build_convertability_detail_rows
from legacydb_doctor.models import ColumnInfo, TableInfo

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


def test_scan_help_includes_readiness_details_option():
    result = runner.invoke(app, ["scan", "--help"])

    assert result.exit_code == 0
    assert "--readiness-details" in result.output
    assert "readiness" in result.output
    assert "details" in result.output


def test_scan_help_includes_convertability_details_option():
    result = runner.invoke(app, ["scan", "--help"])

    assert result.exit_code == 0
    assert "--convertability-details" in result.output
    assert "convertability" in result.output
    assert "details" in result.output

def col(table_name: str, column_name: str) -> ColumnInfo:
    return ColumnInfo(
        table_name=table_name,
        column_name=column_name,
        ordinal_position=None,
        type_name=None,
        data_type=None,
        column_size=None,
        decimal_digits=None,
        nullable=None,
    )


def test_build_convertability_detail_rows_sorts_by_risk():
    tables = [
        TableInfo(
            table_name="ReadyTable",
            row_count=10,
            columns=[col("ReadyTable", "Id")],
            primary_keys=["Id"],
            primary_key_source="unique_index",
        ),
        TableInfo(
            table_name="EmptyDomain",
            row_count=0,
            columns=[],
            primary_keys=["Id"],
            primary_key_source="unique_index",
        ),
        TableInfo(
            table_name="Copy Of OldData",
            row_count=5,
            columns=[col("Copy Of OldData", "Id")],
            primary_keys=["Id"],
            primary_key_source="unique_index",
        ),
        TableInfo(
            table_name="BlockedTable",
            row_count=5,
            columns=[col("BlockedTable", "Name")],
            primary_keys=[],
            primary_key_source="none",
        ),
    ]

    rows = build_convertability_detail_rows(tables)

    assert [row["Status"] for row in rows] == ["Blocked", "Exclude", "Review", "Ready"]
    assert [row["Table"] for row in rows] == [
        "BlockedTable",
        "Copy Of OldData",
        "EmptyDomain",
        "ReadyTable",
    ]

