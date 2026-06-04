from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .access_reader import DEFAULT_ACCESS_DRIVER, AccessConnectionError, inspect_access_database
from .report_writer import write_excel_report
from .sql_writer import write_schema_sql

app = typer.Typer(help="LegacyDB Doctor - Access to MySQL migration readiness toolkit")
console = Console()


@app.callback()
def main() -> None:
    """Inspect legacy Access databases before migrating to MySQL/MariaDB."""


@app.command()
def scan(
    database: Path = typer.Argument(..., help="Path to Access .mdb/.accdb database"),
    out: Path = typer.Option(Path("legacydb_report.xlsx"), "--out", "-o", help="Excel report output path"),
    schema_out: Optional[Path] = typer.Option(Path("schema.sql"), "--schema-out", help="Generated MySQL schema output path. Use empty value to skip."),
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

    report_path = write_excel_report(tables, warnings, out)
    console.print(f"[green]Excel report created:[/green] {report_path}")

    if schema_out is not None:
        schema_path = write_schema_sql(tables, schema_out, use_recommended_names=use_recommended_names)
        console.print(f"[green]Schema SQL created:[/green] {schema_path}")

        if use_recommended_names:
            console.print("[cyan]Schema uses recommended MySQL-safe identifiers.[/cyan]")
        else:
            console.print("[cyan]Schema uses original Access identifiers.[/cyan]")

    summary = Table(title="Scan summary")
    summary.add_column("Metric")
    summary.add_column("Value", justify="right")
    warning_count = sum(1 for item in warnings if item.level == "warning")
    info_count = sum(1 for item in warnings if item.level == "info")

    pk_formal_count = sum(1 for table in tables if table.primary_key_source == "formal")
    pk_unique_index_count = sum(1 for table in tables if table.primary_key_source == "unique_index")
    pk_candidate_count = sum(1 for table in tables if table.primary_key_source == "candidate")
    pk_none_count = sum(1 for table in tables if table.primary_key_source == "none")

    summary.add_row("Tables", str(len(tables)))
    summary.add_row("Columns", str(sum(len(t.columns) for t in tables)))
    summary.add_row("Rows", str(sum(t.row_count or 0 for t in tables)))
    summary.add_row("Warnings", str(warning_count))
    summary.add_row("Info", str(info_count))
    summary.add_row("Total notes", str(len(warnings)))

    summary.add_row("PK formal", str(pk_formal_count))
    summary.add_row("PK unique_index", str(pk_unique_index_count))
    summary.add_row("PK candidate", str(pk_candidate_count))
    summary.add_row("PK none", str(pk_none_count))
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
