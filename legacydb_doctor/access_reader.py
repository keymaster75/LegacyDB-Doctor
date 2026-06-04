from __future__ import annotations

from pathlib import Path
from typing import Iterable

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


def count_rows(cursor: pyodbc.Cursor, table_name: str) -> int | None:
    try:
        safe_name = table_name.replace("]", "]]" )
        row = cursor.execute(f"SELECT COUNT(*) FROM [{safe_name}]").fetchone()
        return int(row[0]) if row else None
    except pyodbc.Error:
        return None


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
        cursor = conn.cursor()
        tables: list[TableInfo] = []
        for table_name in iter_user_tables(cursor):
            row_count = count_rows(cursor, table_name)
            if row_count is None:
                warnings.append(
                    WarningInfo(
                        level="warning",
                        table_name=table_name,
                        column_name=None,
                        message="Could not count rows for this table.",
                    )
                )
            columns = get_columns(cursor, table_name)
            if not columns:
                warnings.append(
                    WarningInfo(
                        level="warning",
                        table_name=table_name,
                        column_name=None,
                        message="No columns detected for this table.",
                    )
                )
            tables.append(TableInfo(table_name=table_name, row_count=row_count, columns=columns))
        return tables, warnings
    finally:
        conn.close()
