from __future__ import annotations

import csv
from pathlib import Path

import pyodbc

from .access_reader import access_identifier, connect_access, iter_user_tables, suggest_mysql_identifier

def write_export_manifest(results: list[dict], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "_export_manifest.csv"

    with manifest_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        fieldnames = ["table", "csv_path", "row_count", "status", "error"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for item in results:
            writer.writerow(
                {
                    "table": item.get("table"),
                    "csv_path": item.get("csv_path"),
                    "row_count": item.get("row_count"),
                    "status": item.get("status"),
                    "error": item.get("error"),
                }
            )

    return manifest_path

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

def filter_table_names(table_names: list[str], table_filter: list[str] | None = None) -> list[str]:
    if not table_filter:
        return table_names

    wanted = {name.strip().lower() for name in table_filter if name.strip()}
    return [name for name in table_names if name.lower() in wanted]

def export_access_tables_to_csv(
    database_path: str | Path,
    output_dir: str | Path,
    driver: str,
    use_recommended_names: bool = False,
    table_filter: list[str] | None = None,
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

        table_names = filter_table_names(table_names, table_filter)

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

        write_export_manifest(results, output)

        return results

    finally:
        conn.close()