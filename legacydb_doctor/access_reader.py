from __future__ import annotations

from pathlib import Path
from typing import Iterable

import re
import unicodedata

import pyodbc

from .models import ColumnInfo, TableInfo, WarningInfo
from .mysql_mapper import map_access_type_to_mysql

DEFAULT_ACCESS_DRIVER = "Microsoft Access Driver (*.mdb, *.accdb)"


class AccessConnectionError(RuntimeError):
    """Raised when the Access database cannot be opened."""


def build_connection_string(database_path: Path, driver: str = DEFAULT_ACCESS_DRIVER) -> str:
    return f"DRIVER={{{driver}}};DBQ={database_path};"


def connect_access(database_path: str | Path, driver: str = DEFAULT_ACCESS_DRIVER) -> pyodbc.Connection:
    db_path = Path(database_path).expanduser().resolve()
    if not db_path.exists():
        raise AccessConnectionError(f"Access database not found: {db_path}")

    try:
        return pyodbc.connect(build_connection_string(db_path, driver), autocommit=True)
    except pyodbc.Error as exc:
        raise AccessConnectionError(
            "Could not open Access database. Check that Microsoft Access ODBC driver is installed. "
            f"Driver used: {driver}. Original error: {exc}"
        ) from exc


def iter_user_tables(cursor: pyodbc.Cursor) -> Iterable[str]:
    for row in cursor.tables(tableType="TABLE"):
        table_name = row.table_name
        if not table_name:
            continue
        # Skip common Access/system artifacts.
        if table_name.startswith("MSys") or table_name.startswith("~"):
            continue
        yield table_name

def suggest_mysql_identifier(name: str) -> str:
    """
    Convert an Access table/column name to a conservative MySQL-friendly identifier.

    Examples:
    - "Copy Of Naslov" -> "copy_of_naslov"
    - "Clan$_ImportErrors" -> "clan_importerrors"
    - "InventarniBroj" -> "inventarni_broj"
    - "Šifra Člana" -> "sifra_clana"
    """
    value = unicodedata.normalize("NFKD", name)
    value = value.encode("ascii", "ignore").decode("ascii")

    # Split CamelCase / PascalCase before lowercasing.
    # Example: InventarniBroj -> Inventarni_Broj
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)

    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value)
    value = value.strip("_")

    if not value:
        value = "unnamed_identifier"

    if value[0].isdigit():
        value = f"t_{value}"

    return value

def detect_suspicious_table_name(table_name: str) -> WarningInfo | None:
    normalized = table_name.lower().strip()
    suggested_name = suggest_mysql_identifier(table_name)

    suspicious_patterns = [
        ("importerrors", "Table looks like an Access import error table."),
        ("import errors", "Table looks like an Access import error table."),
        ("copy of", "Table looks like a backup/copy table."),
        ("copy2 of", "Table looks like a backup/copy table."),
        ("kopija", "Table looks like a backup/copy table."),
        ("backup", "Table looks like a backup table."),
        ("_bak", "Table looks like a backup table."),
        (" bak", "Table looks like a backup table."),
        ("staro", "Table looks like an old/legacy copy table."),
        ("old", "Table looks like an old/legacy copy table."),
        ("temp", "Table looks like a temporary table."),
        ("tmp", "Table looks like a temporary table."),
        ("test", "Table looks like a test table."),
    ]

    for pattern, message in suspicious_patterns:
        if pattern in normalized:
            return WarningInfo(
                level="warning",
                table_name=table_name,
                column_name=None,
                message=f"{message} Suggested MySQL name: `{suggested_name}`.",
            )

    if suggested_name != table_name.lower():
        return WarningInfo(
            level="info",
            table_name=table_name,
            column_name=None,
            message=f"Table name may need normalization for MySQL. Suggested name: `{suggested_name}`.",
        )

    return None

def detect_suspicious_column_name(table_name: str, column_name: str) -> WarningInfo | None:
    suggested_name = suggest_mysql_identifier(column_name)

    if suggested_name != column_name:
        return WarningInfo(
            level="info",
            table_name=table_name,
            column_name=column_name,
            message=f"Column name may need normalization for MySQL. Suggested name: `{suggested_name}`.",
        )

    return None

def access_identifier(name: str) -> str:
    """Quote an Access identifier with square brackets."""
    return "[" + name.replace("]", "]]") + "]"

def count_rows(cursor: pyodbc.Cursor, table_name: str) -> int | None:
    try:
        row = cursor.execute(f"SELECT COUNT(*) FROM {access_identifier(table_name)}").fetchone()
        return int(row[0]) if row else None
    except pyodbc.Error:
        return None

def is_text_column(column: ColumnInfo) -> bool:
    type_name = (column.type_name or "").lower()
    return any(marker in type_name for marker in ["char", "text", "memo", "varchar", "longchar"])


def count_empty_values(cursor: pyodbc.Cursor, table_name: str, column: ColumnInfo) -> int | None:
    try:
        table_sql = access_identifier(table_name)
        column_sql = access_identifier(column.column_name)

        if is_text_column(column):
            row = cursor.execute(
                f"SELECT COUNT(*) FROM {table_sql} WHERE {column_sql} IS NULL OR {column_sql} = ''"
            ).fetchone()
        else:
            row = cursor.execute(
                f"SELECT COUNT(*) FROM {table_sql} WHERE {column_sql} IS NULL"
            ).fetchone()

        return int(row[0]) if row else None

    except pyodbc.Error:
        return None


def profile_columns(conn: pyodbc.Connection, table_name: str, row_count: int | None, columns: list[ColumnInfo]) -> None:
    if row_count is None:
        return

    for column in columns:
        profile_cursor = conn.cursor()
        empty_count = count_empty_values(profile_cursor, table_name, column)
        profile_cursor.close()

        if empty_count is None:
            continue

        filled_count = max(row_count - empty_count, 0)
        fill_rate_percent = round((filled_count / row_count) * 100, 2) if row_count > 0 else 0.0

        column.empty_count = empty_count
        column.filled_count = filled_count
        column.fill_rate_percent = fill_rate_percent

def get_primary_key_columns(cursor: pyodbc.Cursor, table_name: str) -> list[str]:
    primary_keys: list[str] = []

    try:
        for row in cursor.primaryKeys(table=table_name):
            column_name = getattr(row, "column_name", None)
            if column_name and column_name not in primary_keys:
                primary_keys.append(column_name)
    except pyodbc.Error:
        return []

    return primary_keys

def get_unique_index_columns(cursor: pyodbc.Cursor, table_name: str) -> list[str]:
    unique_columns: list[str] = []

    try:
        for row in cursor.statistics(table=table_name, unique=True):
            column_name = getattr(row, "column_name", None)
            index_name = getattr(row, "index_name", "") or ""

            if not column_name:
                continue

            # Skip Access statistics rows that do not describe real columns.
            if column_name not in unique_columns and not index_name.startswith("{"):
                unique_columns.append(column_name)

    except pyodbc.Error:
        return []

    return unique_columns

def guess_primary_key_candidates(columns: list[ColumnInfo]) -> list[str]:
    candidates: list[str] = []

    for column in columns:
        column_name = column.column_name or ""
        normalized_name = column_name.lower()
        type_name = (column.type_name or "").lower()

        # Access AutoNumber is often exposed as COUNTER or AutoNumber-like type.
        if "counter" in type_name or "autoincrement" in type_name or "auto increment" in type_name:
            candidates.append(column_name)
            continue

        # Common ID naming.
        if normalized_name in {"id", "pk", "key"}:
            candidates.append(column_name)
            continue

        # Common Serbian/legacy naming pattern: SifA, SifN, SifC...
        if normalized_name.startswith("sif") and len(normalized_name) <= 8:
            candidates.append(column_name)
            continue

    return candidates

def get_columns(cursor: pyodbc.Cursor, table_name: str) -> list[ColumnInfo]:
    columns: list[ColumnInfo] = []
    for col in cursor.columns(table=table_name):
        type_name = getattr(col, "type_name", None)
        column_size = getattr(col, "column_size", None)
        decimal_digits = getattr(col, "decimal_digits", None)
        nullable_raw = getattr(col, "nullable", None)
        nullable = None if nullable_raw is None else bool(nullable_raw)
        mysql_type = map_access_type_to_mysql(type_name, column_size, decimal_digits)

        columns.append(
            ColumnInfo(
                table_name=table_name,
                column_name=getattr(col, "column_name", ""),
                ordinal_position=getattr(col, "ordinal_position", None),
                type_name=type_name,
                data_type=getattr(col, "data_type", None),
                column_size=column_size,
                decimal_digits=decimal_digits,
                nullable=nullable,
                mysql_type=mysql_type,
            )
        )
    return columns


def inspect_access_database(database_path: str | Path, driver: str = DEFAULT_ACCESS_DRIVER) -> tuple[list[TableInfo], list[WarningInfo]]:
    warnings: list[WarningInfo] = []
    conn = connect_access(database_path, driver=driver)

    try:
        # Important:
        # Do not iterate over cursor.tables() while reusing the same cursor
        # for COUNT(*) and cursor.columns(). Some ODBC drivers reset the active
        # result set, so only the first table is detected.
        table_cursor = conn.cursor()
        table_names = list(iter_user_tables(table_cursor))
        table_cursor.close()

        tables: list[TableInfo] = []

        for table_name in table_names:
            suspicious_warning = detect_suspicious_table_name(table_name)
            if suspicious_warning:
                warnings.append(suspicious_warning)

            row_cursor = conn.cursor()
            row_count = count_rows(row_cursor, table_name)
            row_cursor.close()

            pk_cursor = conn.cursor()
            primary_keys = get_primary_key_columns(pk_cursor, table_name)
            pk_cursor.close()

            primary_key_source = "formal" if primary_keys else "none"

            if row_count is None:
                warnings.append(
                    WarningInfo(
                        level="warning",
                        table_name=table_name,
                        column_name=None,
                        message="Could not count rows for this table.",
                    )
                )

            column_cursor = conn.cursor()
            columns = get_columns(column_cursor, table_name)
            column_cursor.close()

            profile_columns(conn, table_name, row_count, columns)

            if not primary_keys:
                index_cursor = conn.cursor()
                unique_index_columns = get_unique_index_columns(index_cursor, table_name)
                index_cursor.close()

                if unique_index_columns:
                    primary_keys = unique_index_columns
                    primary_key_source = "unique_index"

            if not primary_keys:
                guessed_candidates = guess_primary_key_candidates(columns)

                if guessed_candidates:
                    primary_keys = guessed_candidates
                    primary_key_source = "candidate"
                    warnings.append(
                        WarningInfo(
                            level="info",
                            table_name=table_name,
                            column_name=None,
                            message=f"No formal primary key detected, but possible candidate column(s) found: {', '.join(guessed_candidates)}.",
                        )
                    )
                else:
                    warnings.append(
                        WarningInfo(
                            level="warning",
                            table_name=table_name,
                            column_name=None,
                            message="No primary key or obvious candidate detected. This table may be risky to migrate or synchronize.",
                        )
                    )

            if not columns:
                warnings.append(
                    WarningInfo(
                        level="warning",
                        table_name=table_name,
                        column_name=None,
                        message="No columns detected for this table.",
                    )
                )

            for column in columns:
                column_warning = detect_suspicious_column_name(table_name, column.column_name)
                if column_warning:
                    warnings.append(column_warning)

            tables.append(
                TableInfo(
                    table_name=table_name,
                    row_count=row_count,
                    columns=columns,
                    primary_keys=primary_keys,
                    primary_key_source=primary_key_source,
                )
            )

        return tables, warnings

    finally:
        conn.close()
