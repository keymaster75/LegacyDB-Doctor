from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .access_reader import DEFAULT_ACCESS_DRIVER, AccessConnectionError, inspect_access_database
from .report_writer import write_excel_report
from .summary_builder import build_scan_summary
from .sql_writer import write_schema_sql

import os

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

@app.command("drivers")
def list_drivers() -> None:
    """List installed ODBC drivers."""
    import pyodbc

    table = Table(title="Installed ODBC drivers")
    table.add_column("Driver")
    for item in pyodbc.drivers():
        table.add_row(item)
    console.print(table)
