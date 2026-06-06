from legacydb_doctor.access_reader import guess_potential_relationships
from legacydb_doctor.models import ColumnInfo, TableInfo


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


def test_guess_potential_relationships_matches_child_columns_to_parent_keys():
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

    relationships = guess_potential_relationships(tables)

    assert len(relationships) == 1
    rel = relationships[0]

    assert rel.child_table == "Naslov"
    assert rel.child_column == "SifA"
    assert rel.parent_table == "Autor"
    assert rel.parent_column == "SifA"
    assert rel.confidence == "high"


def test_guess_potential_relationships_ignores_self_relationships():
    tables = [
        TableInfo(
            table_name="Autor",
            columns=[col("Autor", "SifA")],
            primary_keys=["SifA"],
            primary_key_source="unique_index",
        )
    ]

    relationships = guess_potential_relationships(tables)

    assert relationships == []


def test_guess_potential_relationships_ignores_artifact_tables_by_default():
    tables = [
        TableInfo(
            table_name="Clan",
            columns=[col("Clan", "SifC")],
            primary_keys=["SifC"],
            primary_key_source="unique_index",
        ),
        TableInfo(
            table_name="Copy Of Clan",
            columns=[col("Copy Of Clan", "SifC")],
            primary_keys=["SifC"],
            primary_key_source="unique_index",
        ),
        TableInfo(
            table_name="Drzi",
            columns=[col("Drzi", "SifC")],
            primary_keys=[],
            primary_key_source="none",
        ),
    ]

    relationships = guess_potential_relationships(tables)

    assert len(relationships) == 1
    assert relationships[0].child_table == "Drzi"
    assert relationships[0].parent_table == "Clan"


def test_guess_potential_relationships_can_include_artifact_tables():
    tables = [
        TableInfo(
            table_name="Clan",
            columns=[col("Clan", "SifC")],
            primary_keys=["SifC"],
            primary_key_source="unique_index",
        ),
        TableInfo(
            table_name="Copy Of Clan",
            columns=[col("Copy Of Clan", "SifC")],
            primary_keys=["SifC"],
            primary_key_source="unique_index",
        ),
    ]

    relationships = guess_potential_relationships(tables, include_artifact_tables=True)

    assert len(relationships) == 2