from __future__ import annotations


def map_access_type_to_mysql(type_name: str | None, column_size: int | None = None, decimal_digits: int | None = None) -> str:
    """Map Access/ODBC type names to a practical MySQL type.

    ODBC drivers may return slightly different type names. This mapper is intentionally
    conservative and can be improved as real databases are tested.
    """
    if not type_name:
        return "TEXT"

    normalized = type_name.strip().upper()
    size = column_size or 0
    decimals = decimal_digits or 0

    if normalized in {"COUNTER", "AUTOINCREMENT", "AUTO_INCREMENT"}:
        return "INT AUTO_INCREMENT"

    if normalized in {"BYTE", "TINYINT"}:
        return "TINYINT"

    if normalized in {"SHORT", "SMALLINT"}:
        return "SMALLINT"

    if normalized in {"LONG", "INTEGER", "INT"}:
        return "INT"

    if normalized in {"SINGLE", "REAL"}:
        return "FLOAT"

    if normalized in {"DOUBLE", "FLOAT"}:
        return "DOUBLE"

    if normalized in {"DECIMAL", "NUMERIC", "CURRENCY", "MONEY"}:
        precision = min(max(size, 10), 65) if size else 18
        scale = min(max(decimals, 2), 30)
        return f"DECIMAL({precision},{scale})"

    if normalized in {"BIT", "YESNO", "YES/NO", "BOOLEAN", "LOGICAL"}:
        return "TINYINT(1)"

    if normalized in {"DATETIME", "DATE", "TIME", "TIMESTAMP"}:
        return "DATETIME"

    if normalized in {"CHAR", "VARCHAR", "TEXT", "GUID"}:
        if normalized == "GUID":
            return "CHAR(36)"
        if size and size <= 255:
            return f"VARCHAR({size})"
        return "TEXT"

    if normalized in {"LONGCHAR", "LONGTEXT", "MEMO", "NTEXT"}:
        return "TEXT"

    if normalized in {"BINARY", "VARBINARY", "LONGBINARY", "OLE OBJECT"}:
        return "LONGBLOB"

    return "TEXT"
