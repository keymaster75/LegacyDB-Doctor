from __future__ import annotations

from pathlib import Path
from typing import Iterable

import re
import unicodedata

import pyodbc

from .models import ColumnInfo, DuplicateKeyIssue, PotentialRelationshipInfo, RelationshipInfo, TableInfo, WarningInfo
from .mysql_mapper import map_access_type_to_mysql

DEFAULT_ACCESS_DRIVER = "Microsoft Access Driver (*.mdb, *.accdb)"

MYSQL_RISKY_IDENTIFIERS = {
    "accessible",
    "add",
    "all",
    "alter",
    "analyze",
    "and",
    "as",
    "asc",
    "before",
    "between",
    "by",
    "call",
    "case",
    "change",
    "check",
    "column",
    "condition",
    "constraint",
    "create",
    "cross",
    "current_date",
    "current_time",
    "current_timestamp",
    "database",
    "date",
    "day",
    "delete",
    "desc",
    "describe",
    "distinct",
    "drop",
    "each",
    "else",
    "exists",
    "false",
    "for",
    "foreign",
    "from",
    "group",
    "having",
    "if",
    "in",
    "index",
    "inner",
    "insert",
    "interval",
    "into",
    "is",
    "join",
    "key",
    "left",
    "like",
    "limit",
    "lock",
    "long",
    "match",
    "not",
    "null",
    "on",
    "or",
    "order",
    "outer",
    "primary",
    "procedure",
    "range",
    "read",
    "references",
    "right",
    "row",
    "select",
    "set",
    "table",
    "then",
    "to",
    "true",
    "union",
    "unique",
    "update",
    "use",
    "user",
    "values",
    "varchar",
    "view",
    "when",
    "where",
    "with",
    "year",
}


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

def is_mysql_risky_identifier(name: str) -> bool:
    return suggest_mysql_identifier(name) in MYSQL_RISKY_IDENTIFIERS

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

    if suggested_name in MYSQL_RISKY_IDENTIFIERS:
        return WarningInfo(
            level="warning",
            table_name=table_name,
            column_name=None,
            message=f"Table name may conflict with MySQL reserved/risky identifier `{suggested_name}`. Consider renaming it.",
        )

    return None

def is_likely_artifact_table_name(table_name: str) -> bool:
    normalized = table_name.lower().strip()

    artifact_patterns = [
        "importerrors",
        "import errors",
        "copy of",
        "copy2 of",
        "kopija",
        "backup",
        "_bak",
        " bak",
        "staro",
        "old",
        "temp",
        "tmp",
        "test",
    ]

    return any(pattern in normalized for pattern in artifact_patterns)

def detect_suspicious_column_name(table_name: str, column_name: str) -> WarningInfo | None:
    suggested_name = suggest_mysql_identifier(column_name)

    if suggested_name in MYSQL_RISKY_IDENTIFIERS:
        return WarningInfo(
            level="warning",
            table_name=table_name,
            column_name=column_name,
            message=f"Column name may conflict with MySQL reserved/risky identifier `{suggested_name}`. Consider renaming it.",
        )

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

def format_odbc_rule(value: object) -> str | None:
    if value is None:
        return None

    rules = {
        0: "cascade",
        1: "restrict",
        2: "set_null",
        3: "no_action",
        4: "set_default",
    }

    try:
        return rules.get(int(value), str(value))
    except (TypeError, ValueError):
        return str(value)

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
    """
    Return columns from the best unique index candidate.

    Important: Access/ODBC may expose composite unique indexes one column at a time.
    A composite unique index such as (SifN, SifA) does NOT mean that SifN and SifA
    are individually unique. We therefore group rows by index name and prefer a
    single-column unique index when one exists. If only composite unique indexes
    exist, we return the composite column list as a table-level key signal.
    """
    indexes: dict[str, list[tuple[int, str]]] = {}

    try:
        for row in cursor.statistics(table=table_name, unique=True):
            column_name = getattr(row, "column_name", None)
            index_name = getattr(row, "index_name", "") or ""
            ordinal_position = getattr(row, "ordinal_position", None)

            if not column_name:
                continue

            # Skip Access statistics rows that do not describe real columns.
            if index_name.startswith("{"):
                continue

            if not index_name:
                index_name = f"__unnamed_unique_{column_name}"

            try:
                position = int(ordinal_position) if ordinal_position is not None else 999
            except (TypeError, ValueError):
                position = 999

            indexes.setdefault(index_name, []).append((position, column_name))

    except pyodbc.Error:
        return []

    if not indexes:
        return []

    normalized_indexes: list[list[str]] = []
    for columns in indexes.values():
        ordered_columns = [column_name for _, column_name in sorted(columns, key=lambda item: item[0])]
        deduplicated_columns = list(dict.fromkeys(ordered_columns))
        if deduplicated_columns:
            normalized_indexes.append(deduplicated_columns)

    if not normalized_indexes:
        return []

    single_column_indexes = [columns for columns in normalized_indexes if len(columns) == 1]
    if single_column_indexes:
        return single_column_indexes[0]

    # Keep composite unique indexes as a useful table-level key signal.
    # Duplicate checking must treat these as composite, not as separate unique columns.
    return normalized_indexes[0]

def get_relationships(cursor: pyodbc.Cursor, table_names: list[str]) -> list[RelationshipInfo]:
    relationships: list[RelationshipInfo] = []
    seen: set[tuple] = set()

    for table_name in table_names:
        relationship_rows = []

        for kwargs in (
            {"table": table_name},
            {"foreignTable": table_name},
        ):
            try:
                relationship_rows.extend(list(cursor.foreignKeys(**kwargs)))
            except (pyodbc.Error, UnicodeDecodeError, TypeError):
                continue

        for row in relationship_rows:
            parent_table = getattr(row, "pktable_name", None)
            parent_column = getattr(row, "pkcolumn_name", None)
            child_table = getattr(row, "fktable_name", None)
            child_column = getattr(row, "fkcolumn_name", None)
            fk_name = getattr(row, "fk_name", None)

            key = (fk_name, parent_table, parent_column, child_table, child_column)
            if key in seen:
                continue
            seen.add(key)

            relationships.append(
                RelationshipInfo(
                    fk_name=fk_name,
                    parent_table=parent_table,
                    parent_column=parent_column,
                    child_table=child_table,
                    child_column=child_column,
                    update_rule=format_odbc_rule(getattr(row, "update_rule", None)),
                    delete_rule=format_odbc_rule(getattr(row, "delete_rule", None)),
                )
            )

    return relationships

def get_relationships_from_msys(conn: pyodbc.Connection) -> list[RelationshipInfo]:
    relationships: list[RelationshipInfo] = []

    sql = """
        SELECT
            szRelationship,
            szObject,
            szColumn,
            szReferencedObject,
            szReferencedColumn
        FROM MSysRelationships
    """

    try:
        cursor = conn.cursor()
        rows = cursor.execute(sql)
    except pyodbc.Error:
        return relationships

    try:
        for row in rows:
            relationships.append(
                RelationshipInfo(
                    fk_name=getattr(row, "szRelationship", None),
                    parent_table=getattr(row, "szReferencedObject", None),
                    parent_column=getattr(row, "szReferencedColumn", None),
                    child_table=getattr(row, "szObject", None),
                    child_column=getattr(row, "szColumn", None),
                    update_rule=None,
                    delete_rule=None,
                )
            )
    except (pyodbc.Error, UnicodeDecodeError):
        return relationships
    finally:
        cursor.close()

    return relationships

def normalize_column_match_name(name: str | None) -> str:
    if not name:
        return ""

    return suggest_mysql_identifier(name)


def guess_potential_relationships(
    tables: list[TableInfo],
    include_artifact_tables: bool = False,
) -> list[PotentialRelationshipInfo]:
    potential_relationships: list[PotentialRelationshipInfo] = []
    seen: set[tuple[str, str, str, str]] = set()

    parent_candidates: list[tuple[TableInfo, str, str]] = []

    for table in tables:
        if not include_artifact_tables and is_likely_artifact_table_name(table.table_name):
            continue

        # Avoid treating junction/composite-key tables as parent tables in the first heuristic pass.
        # Example: Drzi / Je_Autor often contain multiple FK-like columns and should usually be children.
        if len(table.primary_keys) != 1:
            continue

        parent_key = table.primary_keys[0]
        parent_candidates.append((table, parent_key, table.primary_key_source))

    for child_table in tables:
        if not include_artifact_tables and is_likely_artifact_table_name(child_table.table_name):
            continue

        for child_column in child_table.columns:
            child_column_normalized = normalize_column_match_name(child_column.column_name)

            if not child_column_normalized:
                continue

            for parent_table, parent_column, parent_key_source in parent_candidates:
                if child_table.table_name == parent_table.table_name:
                    continue

                parent_column_normalized = normalize_column_match_name(parent_column)

                if child_column_normalized != parent_column_normalized:
                    continue

                key = (
                    child_table.table_name,
                    child_column.column_name,
                    parent_table.table_name,
                    parent_column,
                )

                if key in seen:
                    continue

                seen.add(key)

                if parent_key_source in {"formal", "unique_index"}:
                    confidence = "high"
                    reason = "Child column matches a single-column parent key."
                elif parent_key_source == "candidate":
                    confidence = "medium"
                    reason = "Child column matches a single-column parent candidate key."
                else:
                    confidence = "low"
                    reason = "Child column matches parent column name."

                potential_relationships.append(
                    PotentialRelationshipInfo(
                        child_table=child_table.table_name,
                        child_column=child_column.column_name,
                        parent_table=parent_table.table_name,
                        parent_column=parent_column,
                        confidence=confidence,
                        reason=reason,
                    )
                )

    return potential_relationships

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

    try:
        column_rows = list(cursor.columns(table=table_name))
    except (pyodbc.Error, UnicodeDecodeError):
        return columns

    for col in column_rows:
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


def format_duplicate_sample_value(value: object) -> str:
    if value is None:
        return "<NULL>"
    return str(value)


def count_duplicate_key_values(
    cursor: pyodbc.Cursor,
    table_name: str,
    column_name: str,
) -> tuple[int, int] | None:
    table_sql = access_identifier(table_name)
    column_sql = access_identifier(column_name)

    sql = f"""
        SELECT COUNT(*) AS duplicate_value_count, SUM(duplicate_row_count) AS affected_rows
        FROM (
            SELECT {column_sql}, COUNT(*) AS duplicate_row_count
            FROM {table_sql}
            GROUP BY {column_sql}
            HAVING COUNT(*) > 1
        ) AS duplicate_groups
    """

    try:
        row = cursor.execute(sql).fetchone()
    except pyodbc.Error:
        return None

    if not row or row[0] is None:
        return (0, 0)

    duplicate_value_count = int(row[0] or 0)
    affected_rows = int(row[1] or 0)

    return duplicate_value_count, affected_rows


def get_duplicate_key_sample_values(
    cursor: pyodbc.Cursor,
    table_name: str,
    column_name: str,
    sample_limit: int = 5,
) -> list[str]:
    table_sql = access_identifier(table_name)
    column_sql = access_identifier(column_name)

    sql = f"""
        SELECT TOP {sample_limit} {column_sql}, COUNT(*) AS duplicate_row_count
        FROM {table_sql}
        GROUP BY {column_sql}
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
    """

    try:
        rows = cursor.execute(sql).fetchall()
    except pyodbc.Error:
        return []

    return [format_duplicate_sample_value(row[0]) for row in rows]


def detect_duplicate_key_issues(
    conn: pyodbc.Connection,
    table_name: str,
    key_columns: list[str],
    key_source: str,
) -> list[DuplicateKeyIssue]:
    if key_source not in {"candidate", "unique_index"}:
        return []

    # A multi-column unique index is a composite key signal, not proof that each
    # individual column is unique. Example: a junction table can be unique on
    # (BookId, AuthorId), while both BookId and AuthorId legitimately repeat.
    # Checking those columns separately would create false duplicate warnings.
    if key_source == "unique_index" and len(key_columns) != 1:
        return []

    issues: list[DuplicateKeyIssue] = []

    for column_name in key_columns:
        count_cursor = conn.cursor()
        duplicate_counts = count_duplicate_key_values(count_cursor, table_name, column_name)
        count_cursor.close()

        if duplicate_counts is None:
            continue

        duplicate_value_count, affected_rows = duplicate_counts

        if duplicate_value_count <= 0:
            continue

        sample_cursor = conn.cursor()
        sample_values = get_duplicate_key_sample_values(sample_cursor, table_name, column_name)
        sample_cursor.close()

        issues.append(
            DuplicateKeyIssue(
                table_name=table_name,
                column_name=column_name,
                key_source=key_source,
                duplicate_value_count=duplicate_value_count,
                affected_rows=affected_rows,
                sample_values=sample_values,
            )
        )

    return issues

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
                        message="No columns detected for this table, or Access ODBC could not read column metadata.",
                    )
                )

            for column in columns:
                column_warning = detect_suspicious_column_name(table_name, column.column_name)
                if column_warning:
                    warnings.append(column_warning)

            table_info = TableInfo(
                table_name=table_name,
                row_count=row_count,
                columns=columns,
                primary_keys=primary_keys,
                primary_key_source=primary_key_source,
            )

            table_info.duplicate_key_issues = detect_duplicate_key_issues(
                conn,
                table_name=table_name,
                key_columns=primary_keys,
                key_source=primary_key_source,
            )

            if table_info.duplicate_key_issues:
                warnings.append(
                    WarningInfo(
                        level="warning",
                        table_name=table_name,
                        column_name=None,
                        message=(
                            f"Duplicate values detected in candidate/key column(s): "
                            f"{', '.join(issue.column_name for issue in table_info.duplicate_key_issues)}."
                        ),
                    )
                )

            tables.append(table_info)

        return tables, warnings

    finally:
        conn.close()
