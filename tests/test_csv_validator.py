import csv

from legacydb_doctor.csv_validator import (
    count_csv_data_rows,
    parse_manifest_row_count,
    validate_csv_export,
)


def write_csv(path, header, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(header)
        writer.writerows(rows)


def write_manifest(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        fieldnames = ["table", "csv_path", "row_count", "status", "error", "export_limit"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_parse_manifest_row_count():
    assert parse_manifest_row_count("10") == 10
    assert parse_manifest_row_count("0") == 0
    assert parse_manifest_row_count("") is None
    assert parse_manifest_row_count(None) is None
    assert parse_manifest_row_count("abc") is None


def test_count_csv_data_rows_counts_rows_without_header(tmp_path):
    csv_path = tmp_path / "autor.csv"
    write_csv(csv_path, ["id", "name"], [[1, "A"], [2, "B"]])

    assert count_csv_data_rows(csv_path) == 2


def test_count_csv_data_rows_empty_file_returns_zero(tmp_path):
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("", encoding="utf-8-sig")

    assert count_csv_data_rows(csv_path) == 0


def test_validate_csv_export_ok_status_matches_existing_csv(tmp_path):
    csv_path = tmp_path / "autor.csv"
    write_csv(csv_path, ["id", "name"], [[1, "A"], [2, "B"]])

    write_manifest(
        tmp_path / "_export_manifest.csv",
        [
            {
                "table": "Autor",
                "csv_path": str(csv_path),
                "row_count": "2",
                "status": "ok",
                "error": "",
                "export_limit": "",
            }
        ],
    )

    results = validate_csv_export(tmp_path)

    assert len(results) == 1
    assert results[0]["level"] == "ok"
    assert "row count matches" in results[0]["message"]


def test_validate_csv_export_detects_missing_csv_file(tmp_path):
    missing_csv = tmp_path / "missing.csv"

    write_manifest(
        tmp_path / "_export_manifest.csv",
        [
            {
                "table": "Autor",
                "csv_path": str(missing_csv),
                "row_count": "2",
                "status": "ok",
                "error": "",
                "export_limit": "",
            }
        ],
    )

    results = validate_csv_export(tmp_path)

    assert len(results) == 1
    assert results[0]["level"] == "error"
    assert "does not exist" in results[0]["message"]


def test_validate_csv_export_detects_row_count_mismatch(tmp_path):
    csv_path = tmp_path / "autor.csv"
    write_csv(csv_path, ["id", "name"], [[1, "A"]])

    write_manifest(
        tmp_path / "_export_manifest.csv",
        [
            {
                "table": "Autor",
                "csv_path": str(csv_path),
                "row_count": "2",
                "status": "ok",
                "error": "",
                "export_limit": "",
            }
        ],
    )

    results = validate_csv_export(tmp_path)

    assert len(results) == 1
    assert results[0]["level"] == "error"
    assert "Row count mismatch" in results[0]["message"]


def test_validate_csv_export_accepts_planned_without_csv_path(tmp_path):
    write_manifest(
        tmp_path / "_export_manifest.csv",
        [
            {
                "table": "Autor",
                "csv_path": "",
                "row_count": "5",
                "status": "planned",
                "error": "",
                "export_limit": "5",
            }
        ],
    )

    results = validate_csv_export(tmp_path)

    assert len(results) == 1
    assert results[0]["level"] == "ok"
    assert "planned" in results[0]["message"]


def test_validate_csv_export_accepts_skipped_empty_without_csv_path(tmp_path):
    write_manifest(
        tmp_path / "_export_manifest.csv",
        [
            {
                "table": "Problem",
                "csv_path": "",
                "row_count": "0",
                "status": "skipped_empty",
                "error": "",
                "export_limit": "",
            }
        ],
    )

    results = validate_csv_export(tmp_path)

    assert len(results) == 1
    assert results[0]["level"] == "ok"
    assert "skipped_empty" in results[0]["message"]


def test_validate_csv_export_missing_manifest_returns_error(tmp_path):
    results = validate_csv_export(tmp_path)

    assert len(results) == 1
    assert results[0]["level"] == "error"
    assert "Manifest file not found" in results[0]["message"]