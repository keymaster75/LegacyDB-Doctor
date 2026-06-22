import json

from legacydb_doctor.html_report_writer import build_html_report, render_html_report_from_json


def sample_payload():
    return {
        "format": "legacydb-doctor-scan-result",
        "format_version": 1,
        "database": {
            "file": "examples/demo_library/legacy_library_demo.mdb",
            "name": "legacy_library_demo.mdb",
            "size_mb": 0.42,
        },
        "summary": {
            "Scan timestamp": "2026-06-22T20:15:30",
            "Tables": 6,
            "Columns": 26,
            "Rows": 25,
            "Migration readiness score": "45 / 100",
            "Migration readiness level": "Low",
            "Convertability ready": 2,
            "Convertability review": 0,
            "Convertability exclude": 2,
            "Convertability blocked": 2,
            "Duplicate key issues": 1,
            "Duplicate key affected rows": 2,
        },
        "readiness": {
            "score": 45,
            "level": "Low",
            "summary": "Database needs significant review before migration.",
            "factors": [],
        },
        "tables": [
            {
                "table_name": "Book",
                "row_count": 6,
                "primary_key_source": "none",
                "convertability_status": "Blocked",
                "convertability_reason": "Table has rows but no detected primary key.",
            },
            {
                "table_name": "Author",
                "row_count": 3,
                "primary_key_source": "unique_index",
                "convertability_status": "Ready",
                "convertability_reason": "Table looks structurally ready for migration.",
            },
        ],
        "warnings": [
            {
                "level": "warning",
                "table_name": "Book",
                "column_name": "InventoryNumber",
                "message": "Duplicate candidate-like key values detected.",
            }
        ],
        "duplicate_key_values": [
            {
                "Severity": "High",
                "Table": "Book",
                "Column": "InventoryNumber",
                "Key Source": "candidate_like",
                "Duplicate Values": 1,
                "Affected Rows": 2,
                "Sample Values": "10012",
                "Recommendation": "Review duplicate values before migration.",
            }
        ],
        "data_quality": [],
        "potential_relationships": [],
        "migration_checklist": [],
    }


def test_build_html_report_contains_key_sections_and_values():
    html = build_html_report(sample_payload())

    assert "<!doctype html>" in html
    assert "LegacyDB Doctor HTML Report" in html
    assert "legacy_library_demo.mdb" in html
    assert "45 / 100" in html
    assert "Low" in html
    assert "Table Convertability" in html
    assert "Duplicate Key Findings" in html
    assert "InventoryNumber" in html
    assert "candidate_like" in html
    assert "Warnings" in html


def test_render_html_report_from_json_writes_file(tmp_path):
    json_file = tmp_path / "scan_result.json"
    output = tmp_path / "scan_report.html"

    json_file.write_text(json.dumps(sample_payload()), encoding="utf-8")

    result = render_html_report_from_json(json_file, output)

    assert result == output
    assert output.exists()
    assert "LegacyDB Doctor HTML Report" in output.read_text(encoding="utf-8")
