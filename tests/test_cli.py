from typer.testing import CliRunner

from legacydb_doctor.cli import app, build_convertability_detail_rows, build_convertability_details_table, build_duplicate_key_detail_rows, build_duplicate_key_details_table
from legacydb_doctor.models import ColumnInfo, DuplicateKeyIssue, TableInfo

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




def test_scan_help_includes_convertability_details_limit_option():
    result = runner.invoke(app, ["scan", "--help"])

    assert result.exit_code == 0
    assert "convertability" in result.output
    assert "limit" in result.output.lower()



def test_build_convertability_details_table_applies_limit():
    tables = [
        TableInfo(
            table_name="BlockedTable",
            row_count=5,
            columns=[col("BlockedTable", "Name")],
            primary_keys=[],
            primary_key_source="none",
        ),
        TableInfo(
            table_name="Copy Of OldData",
            row_count=5,
            columns=[col("Copy Of OldData", "Id")],
            primary_keys=["Id"],
            primary_key_source="unique_index",
        ),
        TableInfo(
            table_name="ReadyTable",
            row_count=10,
            columns=[col("ReadyTable", "Id")],
            primary_keys=["Id"],
            primary_key_source="unique_index",
        ),
    ]

    table = build_convertability_details_table(tables, limit=2)

    assert len(table.rows) == 2



def test_scan_help_includes_convertability_status_option():
    result = runner.invoke(app, ["scan", "--help"])

    assert result.exit_code == 0
    assert "convertability" in result.output
    assert "status" in result.output.lower()



def test_build_convertability_detail_rows_filters_by_status():
    tables = [
        TableInfo(
            table_name="ReadyTable",
            row_count=10,
            columns=[col("ReadyTable", "Id")],
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
        TableInfo(
            table_name="Copy Of OldData",
            row_count=5,
            columns=[col("Copy Of OldData", "Id")],
            primary_keys=["Id"],
            primary_key_source="unique_index",
        ),
    ]

    rows = build_convertability_detail_rows(tables, status_filter="Blocked")

    assert len(rows) == 1
    assert rows[0]["Table"] == "BlockedTable"
    assert rows[0]["Status"] == "Blocked"



def test_build_convertability_detail_rows_filters_by_status_case_insensitive():
    tables = [
        TableInfo(
            table_name="ReadyTable",
            row_count=10,
            columns=[col("ReadyTable", "Id")],
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

    rows = build_convertability_detail_rows(tables, status_filter="ready")

    assert len(rows) == 1
    assert rows[0]["Table"] == "ReadyTable"
    assert rows[0]["Status"] == "Ready"



def test_build_convertability_details_table_applies_status_filter_and_limit():
    tables = [
        TableInfo(
            table_name="BlockedA",
            row_count=5,
            columns=[col("BlockedA", "Name")],
            primary_keys=[],
            primary_key_source="none",
        ),
        TableInfo(
            table_name="BlockedB",
            row_count=7,
            columns=[col("BlockedB", "Name")],
            primary_keys=[],
            primary_key_source="none",
        ),
        TableInfo(
            table_name="ReadyTable",
            row_count=10,
            columns=[col("ReadyTable", "Id")],
            primary_keys=["Id"],
            primary_key_source="unique_index",
        ),
    ]

    table = build_convertability_details_table(tables, limit=1, status_filter="Blocked")

    assert len(table.rows) == 1



def test_scan_help_includes_duplicate_key_details_option():
    result = runner.invoke(app, ["scan", "--help"])

    assert result.exit_code == 0
    assert "duplicate" in result.output.lower()
    assert "key" in result.output.lower()
    assert "details" in result.output.lower()


def test_build_duplicate_key_detail_rows_sorts_by_affected_rows_descending():
    tables = [
        TableInfo(
            table_name="SmallIssue",
            row_count=5,
            columns=[col("SmallIssue", "Code")],
            primary_keys=["Code"],
            primary_key_source="candidate",
            duplicate_key_issues=[
                DuplicateKeyIssue(
                    table_name="SmallIssue",
                    column_name="Code",
                    key_source="candidate",
                    duplicate_value_count=1,
                    affected_rows=2,
                    sample_values=["A"],
                )
            ],
        ),
        TableInfo(
            table_name="LargeIssue",
            row_count=20,
            columns=[col("LargeIssue", "Code")],
            primary_keys=["Code"],
            primary_key_source="candidate",
            duplicate_key_issues=[
                DuplicateKeyIssue(
                    table_name="LargeIssue",
                    column_name="Code",
                    key_source="candidate",
                    duplicate_value_count=3,
                    affected_rows=10,
                    sample_values=["X", "Y"],
                )
            ],
        ),
    ]

    rows = build_duplicate_key_detail_rows(tables)

    assert [row["Table"] for row in rows] == ["LargeIssue", "SmallIssue"]
    assert rows[0]["Duplicate Values"] == "3"
    assert rows[0]["Affected Rows"] == "10"
    assert rows[0]["Sample Values"] == "X, Y"


def test_build_duplicate_key_details_table_has_one_row_per_duplicate_issue():
    tables = [
        TableInfo(
            table_name="LegacyUsers",
            row_count=5,
            columns=[col("LegacyUsers", "SifKorisnika")],
            primary_keys=["SifKorisnika"],
            primary_key_source="candidate",
            duplicate_key_issues=[
                DuplicateKeyIssue(
                    table_name="LegacyUsers",
                    column_name="SifKorisnika",
                    key_source="candidate",
                    duplicate_value_count=2,
                    affected_rows=5,
                    sample_values=["101", "102"],
                )
            ],
        )
    ]

    table = build_duplicate_key_details_table(tables)

    assert len(table.rows) == 1



def test_generate_import_sql_help_mentions_manifest_and_output():
    result = runner.invoke(app, ["generate-import-sql", "--help"])

    assert result.exit_code == 0
    assert "import" in result.output.lower()
    assert "sql" in result.output.lower()
    assert "manifest" in result.output.lower()
    assert "out" in result.output.lower()
