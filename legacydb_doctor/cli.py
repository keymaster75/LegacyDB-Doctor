from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .access_reader import DEFAULT_ACCESS_DRIVER, AccessConnectionError, inspect_access_database
from .csv_exporter import export_access_tables_to_csv
from .report_writer import write_excel_report
from .summary_builder import build_scan_summary
from .sql_writer import write_schema_sql
app = typer.Typer(help="LegacyDB Doctor - Access to MySQL migration readiness toolkit")
console = Console()


@app.callback()
def main() -> None:
    """Inspect legacy Access databases before migrating to MySQL/MariaDB."""


def build_default_output_paths(database: Path, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    database_stem = database.stem
    report_path = output_dir / f"{database_stem}_report.xlsx"
    schema_path = output_dir / f"{database_stem}_schema.sql"

    return report_path, schema_path


@app.command()
def scan(
    database: Path = typer.Argument(..., help="Path to Access .mdb/.accdb database"),
    out: Path = typer.Option(Path("legacydb_report.xlsx"), "--out", "-o", help="Excel report output path"),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        help="Output directory for generated report and schema. File names are based on the database name.",
    ),
    open_report: bool = typer.Option(
        False,
        "--open-report",
        help="Open the generated Excel report after scan completion.",
    ),
    schema_out: Optional[Path] = typer.Option(
        Path("schema.sql"),
        "--schema-out",
        help="Generated MySQL schema output path.",
    ),
    no_schema: bool = typer.Option(
        False,
        "--no-schema",
        "--report-only",
        help="Skip schema.sql generation and create only the Excel report.",
    ),
    summary_only: bool = typer.Option(
        False,
        "--summary-only",
        help="Only print scan summary; skip Excel report and schema generation.",
    ),
    driver: str = typer.Option(DEFAULT_ACCESS_DRIVER, "--driver", help="ODBC driver name"),
    use_recommended_names: bool = typer.Option(
        False,
        "--use-recommended-names",
        help="Use normalized MySQL-safe table and column names in generated schema.sql.",
    ),
) -> None:
    """Scan an Access database and generate migration-readiness outputs."""
    console.print(f"[bold]LegacyDB Doctor[/bold] scanning: {database}")

    try:
        tables, warnings = inspect_access_database(database, driver=driver)
    except AccessConnectionError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    if output_dir is not None:
        out, schema_out = build_default_output_paths(database, output_dir)

    if summary_only:
        console.print("[yellow]Summary-only mode: Excel report and schema SQL generation skipped.[/yellow]")
    else:
        report_path = write_excel_report(tables, warnings, out)
        console.print(f"[green]Excel report created:[/green] {report_path}")

        if open_report:
            try:
                os.startfile(report_path)
            except OSError as exc:
                console.print(f"[yellow]Could not open report automatically:[/yellow] {exc}")

        if no_schema:
            console.print("[yellow]Schema SQL generation skipped.[/yellow]")
        elif schema_out is not None:
            schema_path = write_schema_sql(tables, schema_out, use_recommended_names=use_recommended_names)
            console.print(f"[green]Schema SQL created:[/green] {schema_path}")

            if use_recommended_names:
                console.print("[cyan]Schema uses recommended MySQL-safe identifiers.[/cyan]")
            else:
                console.print("[cyan]Schema uses original Access identifiers.[/cyan]")

    summary = Table(title="Scan summary")
    summary.add_column("Metric")
    summary.add_column("Value", justify="right")

    for row in build_scan_summary(tables, warnings):
        summary.add_row(str(row["Metric"]), str(row["Value"]))

    console.print(summary)


@app.command("export-csv")
def export_csv(
    database: Path = typer.Argument(..., help="Path to Access .mdb/.accdb database"),
    output_dir: Path = typer.Option(..., "--output-dir", "-o", help="Directory where CSV files will be created."),
    tables: Optional[str] = typer.Option(
        None,
        "--tables",
        help="Comma-separated list of Access table names to export, e.g. Autor,Naslov,Clan.",
    ),
    skip_empty: bool = typer.Option(
        False,
        "--skip-empty",
        help="Skip exporting empty tables and record them as skipped_empty in the manifest.",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        min=1,
        help="Export at most N rows per table. Useful for sampling large databases.",
    ),
    driver: str = typer.Option(DEFAULT_ACCESS_DRIVER, "--driver", help="ODBC driver name"),
    use_recommended_names: bool = typer.Option(
        False,
        "--use-recommended-names",
        help="Use normalized MySQL-safe names for CSV file names.",
    ),
) -> None:
    """Export Access user tables to CSV files."""
    console.print(f"[bold]LegacyDB Doctor[/bold] exporting CSV files from: {database}")

    table_filter = None
    if tables:
        table_filter = [item.strip() for item in tables.split(",") if item.strip()]
        console.print(f"[cyan]Table filter:[/cyan] {', '.join(table_filter)}")

    try:
        results = export_access_tables_to_csv(
            database_path=database,
            output_dir=output_dir,
            driver=driver,
            use_recommended_names=use_recommended_names,
            table_filter=table_filter,
            skip_empty=skip_empty,
            limit=limit,
        )
    except AccessConnectionError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    ok_count = sum(1 for item in results if item["status"] == "ok")
    error_count = sum(1 for item in results if item["status"] == "error")
    total_rows = sum(item["row_count"] or 0 for item in results)

    skipped_empty_count = sum(1 for item in results if item["status"] == "skipped_empty")

    if table_filter and not results:
        console.print("[yellow]No matching tables found for the provided --tables filter.[/yellow]")

    table = Table(title="CSV export summary")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Tables exported", str(ok_count))
    table.add_row("Tables failed", str(error_count))
    table.add_row("Tables skipped empty", str(skipped_empty_count))
    table.add_row("Rows exported", str(total_rows))
    table.add_row("Output directory", str(output_dir))
    console.print(table)

    if error_count:
        error_table = Table(title="CSV export errors")
        error_table.add_column("Table")
        error_table.add_column("Error")

        for item in results:
            if item["status"] == "error":
                error_table.add_row(str(item["table"]), str(item["error"]))

        console.print(error_table)


@app.command("drivers")
def list_drivers() -> None:
    """List installed ODBC drivers."""
    import pyodbc

    table = Table(title="Installed ODBC drivers")
    table.add_column("Driver")
    for item in pyodbc.drivers():
        table.add_row(item)
    console.print(table)
