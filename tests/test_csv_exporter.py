import csv

from legacydb_doctor.csv_exporter import filter_table_names, write_export_manifest


def test_write_export_manifest_creates_manifest_for_results(tmp_path):
    results = [
        {
            "table": "Autor",
            "csv_path": str(tmp_path / "autor.csv"),
            "row_count": 10,
            "status": "ok",
            "error": None,
        },
        {
            "table": "Problem",
            "csv_path": None,
            "row_count": None,
            "status": "error",
            "error": "Example error",
        },
    ]

    manifest_path = write_export_manifest(results, tmp_path)

    assert manifest_path.exists()

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 2
    assert rows[0]["table"] == "Autor"
    assert rows[0]["row_count"] == "10"
    assert rows[0]["status"] == "ok"
    assert rows[1]["table"] == "Problem"
    assert rows[1]["status"] == "error"
    assert rows[1]["error"] == "Example error"


def test_write_export_manifest_creates_folder_for_empty_results(tmp_path):
    output_dir = tmp_path / "missing_folder"

    manifest_path = write_export_manifest([], output_dir)

    assert output_dir.exists()
    assert manifest_path.exists()

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows == []

def test_filter_table_names_returns_all_when_no_filter():
    table_names = ["Autor", "Naslov", "Clan"]

    assert filter_table_names(table_names, None) == table_names


def test_filter_table_names_matches_case_insensitive_names():
    table_names = ["Autor", "Naslov", "Clan", "Drzi"]

    result = filter_table_names(table_names, ["autor", "CLAN"])

    assert result == ["Autor", "Clan"]


def test_filter_table_names_returns_empty_when_no_match():
    table_names = ["Autor", "Naslov", "Clan"]

    result = filter_table_names(table_names, ["NePostoji"])

    assert result == []