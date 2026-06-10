from pathlib import Path

from legacydb_doctor.models import ColumnInfo, TableInfo, WarningInfo
from legacydb_doctor.summary_builder import build_scan_summary


def test_build_scan_summary_counts_tables_columns_rows_warnings_pk_and_dq():
    tables = [
        TableInfo(
            table_name="Autor",
            row_count=10,
            columns=[
                ColumnInfo(
                    table_name="Autor",
                    column_name="SifA",
                    ordinal_position=1,
                    type_name="COUNTER",
                    data_type=None,
                    column_size=None,
                    decimal_digits=None,
                    nullable=False,
                    mysql_type="INT AUTO_INCREMENT",
                    empty_count=0,
                    filled_count=10,
                    fill_rate_percent=100.0,
                ),
                ColumnInfo(
                    table_name="Autor",
                    column_name="Napomena",
                    ordinal_position=2,
                    type_name="TEXT",
                    data_type=None,
                    column_size=255,
                    decimal_digits=None,
                    nullable=True,
                    mysql_type="VARCHAR(255)",
                    empty_count=10,
                    filled_count=0,
                    fill_rate_percent=0.0,
                ),
            ],
            primary_keys=["SifA"],
            primary_key_source="unique_index",
        ),
        TableInfo(
            table_name="Problem",
            row_count=0,
            columns=[],
            primary_keys=[],
            primary_key_source="none",
        ),
    ]

    warnings = [
        WarningInfo(
            level="warning",
            table_name="Problem",
            column_name=None,
            message="No primary key detected.",
        ),
        WarningInfo(
            level="info",
            table_name="Autor",
            column_name="Napomena",
            message="Column name may need normalization.",
        ),
    ]

    summary = build_scan_summary(tables, warnings)
    summary_dict = {row["Metric"]: row["Value"] for row in summary}

    assert summary_dict["Tables"] == 2
    assert summary_dict["Columns"] == 2
    assert summary_dict["Rows"] == 10
    assert summary_dict["Warnings"] == 1
    assert summary_dict["Info"] == 1
    assert summary_dict["Total notes"] == 2
    assert summary_dict["Migration readiness score"] == "72 / 100"
    assert summary_dict["Migration readiness level"] == "Medium"
    assert summary_dict["Convertability ready"] == 1
    assert summary_dict["Convertability review"] == 1
    assert summary_dict["Convertability exclude"] == 0
    assert summary_dict["Convertability blocked"] == 0
    assert summary_dict["PK formal"] == 0
    assert summary_dict["PK unique_index"] == 1
    assert summary_dict["PK candidate"] == 0
    assert summary_dict["PK none"] == 1
    assert summary_dict["DQ high"] == 1
    assert summary_dict["DQ medium"] == 0
    assert summary_dict["DQ low"] == 0

def make_column(table_name: str, column_name: str) -> ColumnInfo:
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


def test_build_scan_summary_includes_potential_relationship_count():
    tables = [
        TableInfo(
            table_name="Autor",
            row_count=2,
            columns=[
                make_column("Autor", "SifA"),
                make_column("Autor", "Ime"),
            ],
            primary_keys=["SifA"],
            primary_key_source="unique_index",
        ),
        TableInfo(
            table_name="Naslov",
            row_count=5,
            columns=[
                make_column("Naslov", "SifN"),
                make_column("Naslov", "SifA"),
            ],
            primary_keys=["SifN"],
            primary_key_source="unique_index",
        ),
    ]

    summary = build_scan_summary(tables, warnings=[])
    summary_dict = {row["Metric"]: row["Value"] for row in summary}

    assert summary_dict["Potential relationships"] == 1


def test_build_scan_summary_shows_high_readiness_for_clean_database():
    tables = [
        TableInfo(
            table_name="Autor",
            row_count=10,
            columns=[
                make_column("Autor", "SifA"),
                make_column("Autor", "Ime"),
            ],
            primary_keys=["SifA"],
            primary_key_source="unique_index",
        ),
        TableInfo(
            table_name="Naslov",
            row_count=20,
            columns=[
                make_column("Naslov", "SifN"),
                make_column("Naslov", "Naziv"),
                make_column("Naslov", "SifA"),
            ],
            primary_keys=["SifN"],
            primary_key_source="unique_index",
        ),
    ]

    summary = build_scan_summary(tables, warnings=[])
    summary_dict = {row["Metric"]: row["Value"] for row in summary}

    assert summary_dict["Migration readiness score"] == "100 / 100"
    assert summary_dict["Migration readiness level"] == "High"


def test_build_scan_summary_includes_database_metadata(tmp_path):
    database = tmp_path / "Library.mdb"
    database.write_bytes(b"legacydb-test")

    tables = [
        TableInfo(
            table_name="Autor",
            row_count=10,
            columns=[make_column("Autor", "SifA")],
            primary_keys=["SifA"],
            primary_key_source="unique_index",
        )
    ]

    summary = build_scan_summary(tables, warnings=[], database_path=database)
    summary_dict = {row["Metric"]: row["Value"] for row in summary}

    assert summary_dict["Database file"] == str(database)
    assert summary_dict["Database name"] == "Library.mdb"
    assert summary_dict["Database size MB"] == "0.00"
    assert "T" in summary_dict["Scan timestamp"]



def test_build_scan_summary_includes_convertability_counts():
    tables = [
        TableInfo(
            table_name="ReadyTable",
            row_count=10,
            columns=[make_column("ReadyTable", "Id")],
            primary_keys=["Id"],
            primary_key_source="unique_index",
        ),
        TableInfo(
            table_name="BlockedTable",
            row_count=5,
            columns=[make_column("BlockedTable", "Name")],
            primary_keys=[],
            primary_key_source="none",
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
            columns=[make_column("Copy Of OldData", "Id")],
            primary_keys=["Id"],
            primary_key_source="unique_index",
        ),
    ]

    summary = build_scan_summary(tables, warnings=[])
    summary_dict = {row["Metric"]: row["Value"] for row in summary}

    assert summary_dict["Convertability ready"] == 1
    assert summary_dict["Convertability review"] == 1
    assert summary_dict["Convertability exclude"] == 1
    assert summary_dict["Convertability blocked"] == 1
