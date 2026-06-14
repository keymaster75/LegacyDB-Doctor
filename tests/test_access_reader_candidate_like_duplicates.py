from legacydb_doctor.access_reader import guess_candidate_like_key_columns, is_candidate_like_key_column
from legacydb_doctor.models import ColumnInfo


def make_column(name: str, type_name: str | None = "INTEGER") -> ColumnInfo:
    return ColumnInfo(
        table_name="Book",
        column_name=name,
        ordinal_position=None,
        type_name=type_name,
        data_type=None,
        column_size=None,
        decimal_digits=None,
        nullable=None,
    )


def test_is_candidate_like_key_column_detects_inventory_number():
    assert is_candidate_like_key_column(make_column("InventoryNumber")) is True


def test_is_candidate_like_key_column_avoids_plain_title_text():
    assert is_candidate_like_key_column(make_column("Title", "VARCHAR")) is False


def test_guess_candidate_like_key_columns_returns_business_key_like_columns():
    columns = [
        make_column("InventoryNumber"),
        make_column("Title", "VARCHAR"),
        make_column("BookID"),
    ]

    assert guess_candidate_like_key_columns(columns) == ["InventoryNumber", "BookID"]
