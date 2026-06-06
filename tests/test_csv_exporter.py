import csv

from legacydb_doctor.csv_exporter import build_select_sql, filter_table_names, write_export_manifest

def test_write_export_manifest_creates_manifest_for_results(tmp_path):
    results = [
        {
            "table": "Autor",
            "csv_path": str(tmp_path / "autor.csv"),
            "row_count": 10,
            "status": "ok",
            "error": None,
            "export_limit": 100,
        },
        {
            "table": "Problem",
            "csv_path": None,
            "row_count": None,
            "status": "error",
            "error": "Example error",
            "export_limit": 100,
        },
        {
            "table": "Razredni",
            "csv_path": None,
            "row_count": 0,
            "status": "skipped_empty",
            "error": None,
            "export_limit": 100,
        },
        {
            "table": "Naslov",
            "csv_path": None,
            "row_count": 5,
            "status": "planned",
            "error": None,
            "export_limit": 5,
        },
    ]

    manifest_path = write_export_manifest(results, tmp_path)

    assert manifest_path.exists()

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 4
    assert rows[0]["table"] == "Autor"
    assert rows[0]["row_count"] == "10"
    assert rows[0]["status"] == "ok"
    assert rows[1]["table"] == "Problem"
    assert rows[1]["status"] == "error"
    assert rows[1]["error"] == "Example error"
    assert rows[2]["table"] == "Razredni"
    assert rows[2]["row_count"] == "0"
    assert rows[2]["status"] == "skipped_empty"
    assert rows[0]["export_limit"] == "100"
    assert rows[2]["export_limit"] == "100"
    assert rows[3]["table"] == "Naslov"
    assert rows[3]["row_count"] == "5"
    assert rows[3]["status"] == "planned"
    assert rows[3]["export_limit"] == "5"

def test_write_export_manifest_creates_folder_for_empty_results(tmp_path):
    output_dir = tmp_path / "missing_folder"

    manifest_path = write_export_manifest([], output_dir)

    assert output_dir.exists()
    assert manifest_path.exists()

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    assert reader.fieldnames == ["table", "csv_path", "row_count", "status", "error", "export_limit"]
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

def test_build_select_sql_without_limit():
    assert build_select_sql("Autor") == "SELECT * FROM [Autor]"


def test_build_select_sql_with_limit():
    assert build_select_sql("Autor", 5) == "SELECT TOP 5 * FROM [Autor]"


def test_build_select_sql_ignores_zero_or_negative_limit():
    assert build_select_sql("Autor", 0) == "SELECT * FROM [Autor]"
    assert build_select_sql("Autor", -1) == "SELECT * FROM [Autor]"


def test_build_select_sql_quotes_access_table_names():
    assert build_select_sql("Copy Of Naslov", 10) == "SELECT TOP 10 * FROM [Copy Of Naslov]"