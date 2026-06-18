from pathlib import Path
import json

from legacydb_doctor.json_writer import build_scan_json_payload, write_scan_json
from legacydb_doctor.models import ColumnInfo, DuplicateKeyIssue, TableInfo, WarningInfo


def col(table_name: str, column_name: str, fill_rate_percent=None) -> ColumnInfo:
    return ColumnInfo(
        table_name=table_name,
        column_name=column_name,
        ordinal_position=1,
        type_name="TEXT",
        data_type=None,
        column_size=255,
        decimal_digits=None,
        nullable=True,
        mysql_type="VARCHAR(255)",
        empty_count=0,
        filled_count=1,
        fill_rate_percent=fill_rate_percent,
    )


def test_build_scan_json_payload_includes_summary_tables_warnings_and_readiness(tmp_path):
    database = tmp_path / "Library.mdb"
    database.write_bytes(b"legacydb-json-test")

    tables = [
        TableInfo(
            table_name="Book",
            row_count=2,
            columns=[col("Book", "InventoryNumber")],
            primary_keys=[],
            primary_key_source="none",
            duplicate_key_issues=[
                DuplicateKeyIssue(
                    table_name="Book",
                    column_name="InventoryNumber",
                    key_source="candidate_like",
                    duplicate_value_count=1,
                    affected_rows=2,
                    sample_values=["10012"],
                )
            ],
        )
    ]
    warnings = [
        WarningInfo(
            level="warning",
            table_name="Book",
            column_name="InventoryNumber",
            message="Candidate-like key column contains duplicate values.",
        )
    ]

    payload = build_scan_json_payload(tables, warnings, database_path=database)

    assert payload["format"] == "legacydb-doctor-scan-result"
    assert payload["format_version"] == 1
    assert payload["database"]["name"] == "Library.mdb"
    assert payload["summary"]["Tables"] == 1
    assert payload["summary"]["Duplicate key issues"] == 1
    assert payload["readiness"]["level"] in {"High", "Medium", "Low"}

    assert len(payload["tables"]) == 1
    assert payload["tables"][0]["table_name"] == "Book"
    assert payload["tables"][0]["convertability_status"] == "Blocked"
    assert payload["tables"][0]["duplicate_key_issues"][0]["key_source"] == "candidate_like"

    assert payload["warnings"][0]["level"] == "warning"
    assert payload["duplicate_key_values"][0]["Key Source"] == "candidate_like"
    assert "migration_checklist" in payload


def test_write_scan_json_creates_utf8_json_file(tmp_path):
    output = tmp_path / "scan_result.json"
    tables = [
        TableInfo(
            table_name="Author",
            row_count=1,
            columns=[col("Author", "AuthorID")],
            primary_keys=["AuthorID"],
            primary_key_source="unique_index",
        )
    ]

    result_path = write_scan_json(tables, warnings=[], output_path=output)

    assert result_path == output
    assert output.exists()

    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["summary"]["Tables"] == 1
    assert payload["tables"][0]["table_name"] == "Author"
    assert payload["tables"][0]["convertability_status"] == "Ready"
