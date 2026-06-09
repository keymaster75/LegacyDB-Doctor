from legacydb_doctor.models import ColumnInfo, TableInfo, WarningInfo
from legacydb_doctor.report_writer import build_report_frames


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


def test_build_report_frames_includes_potential_relationships_sheet():
    tables = [
        TableInfo(
            table_name="Autor",
            columns=[col("Autor", "SifA"), col("Autor", "Ime")],
            primary_keys=["SifA"],
            primary_key_source="unique_index",
        ),
        TableInfo(
            table_name="Naslov",
            columns=[col("Naslov", "SifN"), col("Naslov", "SifA")],
            primary_keys=["SifN"],
            primary_key_source="unique_index",
        ),
    ]

    frames = build_report_frames(tables, warnings=[])

    assert "Potential Relationships" in frames

    df = frames["Potential Relationships"]

    assert len(df) == 1
    assert df.iloc[0]["Child Table"] == "Naslov"
    assert df.iloc[0]["Child Column"] == "SifA"
    assert df.iloc[0]["Parent Table"] == "Autor"
    assert df.iloc[0]["Parent Column"] == "SifA"
    assert df.iloc[0]["Confidence"] == "high"


def test_build_report_frames_includes_empty_potential_relationships_message():
    tables = [
        TableInfo(
            table_name="Autor",
            columns=[col("Autor", "SifA")],
            primary_keys=["SifA"],
            primary_key_source="unique_index",
        )
    ]

    frames = build_report_frames(tables, warnings=[])

    df = frames["Potential Relationships"]

    assert len(df) == 1
    assert df.iloc[0]["Reason"] == "No potential relationships detected."


def test_build_report_frames_includes_fk_suggestions_sheet():
    tables = [
        TableInfo(
            table_name="Autor",
            columns=[col("Autor", "SifA"), col("Autor", "Ime")],
            primary_keys=["SifA"],
            primary_key_source="unique_index",
        ),
        TableInfo(
            table_name="Naslov",
            columns=[col("Naslov", "SifN"), col("Naslov", "SifA")],
            primary_keys=["SifN"],
            primary_key_source="unique_index",
        ),
    ]

    frames = build_report_frames(tables, warnings=[])

    assert "FK Suggestions" in frames

    df = frames["FK Suggestions"]

    assert len(df) == 1
    assert df.iloc[0]["Child Table"] == "Naslov"
    assert df.iloc[0]["Child Column"] == "SifA"
    assert df.iloc[0]["Parent Table"] == "Autor"
    assert df.iloc[0]["Parent Column"] == "SifA"
    assert df.iloc[0]["Confidence"] == "high"
    assert (
        df.iloc[0]["Suggestion"]
        == "-- FK suggestion: `naslov`.`sif_a` may reference `autor`.`sif_a`"
    )


def test_build_report_frames_includes_empty_fk_suggestions_message():
    tables = [
        TableInfo(
            table_name="Autor",
            columns=[col("Autor", "SifA")],
            primary_keys=["SifA"],
            primary_key_source="unique_index",
        )
    ]

    frames = build_report_frames(tables, warnings=[])

    df = frames["FK Suggestions"]

    assert len(df) == 1
    assert df.iloc[0]["Reason"] == "No FK suggestions generated."


def test_build_report_frames_includes_readiness_factors_sheet():
    tables = [
        TableInfo(
            table_name="Autor",
            row_count=10,
            columns=[col("Autor", "SifA"), col("Autor", "Ime")],
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
        )
    ]

    frames = build_report_frames(tables, warnings=warnings)

    assert "Readiness Factors" in frames

    df = frames["Readiness Factors"]

    assert list(df.columns) == ["Factor", "Impact", "Severity", "Message", "Recommendation"]
    assert df.iloc[0]["Factor"] == "Overall readiness"
    assert df.iloc[0]["Severity"] == "Medium"
    assert "conservative planning indicator" in df.iloc[0]["Recommendation"]
    assert "Tables without primary key or unique index" in set(df["Factor"])
    assert "Migration warnings" in set(df["Factor"])


def test_build_report_frames_includes_migration_checklist_sheet():
    tables = [
        TableInfo(
            table_name="Autor",
            row_count=10,
            columns=[col("Autor", "SifA"), col("Autor", "Ime")],
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
        )
    ]

    frames = build_report_frames(tables, warnings=warnings)

    assert "Migration Checklist" in frames

    df = frames["Migration Checklist"]

    assert list(df.columns) == ["Area", "Status", "Finding", "Recommended Action", "Related Sheet"]
    assert "Readiness score" in set(df["Area"])
    assert "Primary keys" in set(df["Area"])
    assert "Data quality" in set(df["Area"])
    assert "Cleanup" in set(df["Area"])
    assert "Warnings" in set(df["Area"])

    primary_keys_row = df[df["Area"] == "Primary keys"].iloc[0]
    assert primary_keys_row["Status"] == "Fail"
    assert "no detected primary key" in primary_keys_row["Finding"]

    readiness_row = df[df["Area"] == "Readiness score"].iloc[0]
    assert readiness_row["Related Sheet"] == "Readiness Factors"

