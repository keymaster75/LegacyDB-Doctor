from __future__ import annotations

import csv
from pathlib import Path

import pyodbc

from .access_reader import access_identifier, connect_access, iter_user_tables, suggest_mysql_identifier


def export_table_to_csv(
    conn: pyodbc.Connection,
    table_name: str,
    output_dir: Path,
    use_recommended_names: bool = False,
) -> tuple[Path | None, int | None, str | None]:
    """
    Export a single Access table to CSV.

    Returns:
        (csv_path, row_count, error_message)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    file_stem = suggest_mysql_identifier(table_name) if use_recommended_names else table_name
    safe_file_stem = suggest_mysql_identifier(file_stem)
    csv_path = output_dir / f"{safe_file_stem}.csv"

    try:
        cursor = conn.cursor()
        rows = cursor.execute(f"SELECT * FROM {access_identifier(table_name)}")
        columns = [column[0] for column in rows.description]

        row_count = 0

        with csv_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(columns)

            for row in rows:
                writer.writerow(list(row))
                row_count += 1

        cursor.close()
        return csv_path, row_count, None

    except Exception as exc:
        return None, None, str(exc)


def export_access_tables_to_csv(
    database_path: str | Path,
    output_dir: str | Path,
    driver: str,
    use_recommended_names: bool = False,
) -> list[dict]:
    """
    Export all user Access tables to CSV files.

    Returns a list of export result dictionaries.
    """
    output = Path(output_dir)
    conn = connect_access(database_path, driver=driver)

    try:
        table_cursor = conn.cursor()
        table_names = list(iter_user_tables(table_cursor))
        table_cursor.close()

        results: list[dict] = []

        for table_name in table_names:
            csv_path, row_count, error = export_table_to_csv(
                conn=conn,
                table_name=table_name,
                output_dir=output,
                use_recommended_names=use_recommended_names,
            )

            results.append(
                {
                    "table": table_name,
                    "csv_path": str(csv_path) if csv_path else None,
                    "row_count": row_count,
                    "status": "ok" if error is None else "error",
                    "error": error,
                }
            )

        return results

    finally:
        conn.close()