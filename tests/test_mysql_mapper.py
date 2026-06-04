from legacydb_doctor.mysql_mapper import map_access_type_to_mysql


def test_text_mapping_with_size():
    assert map_access_type_to_mysql("TEXT", 100) == "VARCHAR(100)"


def test_text_mapping_large_size():
    assert map_access_type_to_mysql("TEXT", 500) == "TEXT"


def test_boolean_mapping():
    assert map_access_type_to_mysql("YESNO") == "TINYINT(1)"


def test_datetime_mapping():
    assert map_access_type_to_mysql("DATETIME") == "DATETIME"
