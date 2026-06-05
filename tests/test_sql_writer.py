from legacydb_doctor.models import ColumnInfo, TableInfo
from legacydb_doctor.sql_writer import create_schema_sql


def test_create_schema_sql_with_recommended_names_and_unique_key():
    table = TableInfo(
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
            ),
            ColumnInfo(
                table_name="Autor",
                column_name="Ime",
                ordinal_position=2,
                type_name="TEXT",
                data_type=None,
                column_size=60,
                decimal_digits=None,
                nullable=True,
                mysql_type="VARCHAR(60)",
            ),
        ],
        primary_keys=["SifA"],
        primary_key_source="unique_index",
    )

    sql = create_schema_sql([table], use_recommended_names=True)

    assert "CREATE TABLE `autor`" in sql
    assert "`sif_a` INT AUTO_INCREMENT NOT NULL" in sql
    assert "`ime` VARCHAR(60) NULL" in sql
    assert "UNIQUE KEY `uk_autor_sif_a` (`sif_a`)" in sql


def test_create_schema_sql_warns_when_no_key_detected():
    table = TableInfo(
        table_name="Problem",
        row_count=0,
        columns=[
            ColumnInfo(
                table_name="Problem",
                column_name="Opis",
                ordinal_position=1,
                type_name="MEMO",
                data_type=None,
                column_size=None,
                decimal_digits=None,
                nullable=True,
                mysql_type="TEXT",
            )
        ],
        primary_keys=[],
        primary_key_source="none",
    )

    sql = create_schema_sql([table], use_recommended_names=True)

    assert "-- Warning: no primary key or unique index detected for table `problem`" in sql
    assert "CREATE TABLE `problem`" in sql
    assert "`opis` TEXT NULL" in sql