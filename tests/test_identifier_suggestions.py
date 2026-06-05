from legacydb_doctor.access_reader import suggest_mysql_identifier


def test_suggest_mysql_identifier_normalizes_access_names():
    assert suggest_mysql_identifier("Copy Of Naslov") == "copy_of_naslov"
    assert suggest_mysql_identifier("Clan$_ImportErrors") == "clan_import_errors"
    assert suggest_mysql_identifier("InventarniBroj") == "inventarni_broj"
    assert suggest_mysql_identifier("DatumPro") == "datum_pro"
    assert suggest_mysql_identifier("Šifra Člana") == "sifra_clana"


def test_suggest_mysql_identifier_handles_edge_cases():
    assert suggest_mysql_identifier("123Tabela") == "t_123_tabela"
    assert suggest_mysql_identifier("   ") == "unnamed_identifier"
    assert suggest_mysql_identifier("A---B___C") == "a_b_c"