from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .access_reader import DEFAULT_ACCESS_DRIVER, AccessConnectionError, inspect_access_database
from .csv_exporter import export_access_tables_to_csv
from .fk_suggestions_writer import write_fk_suggestions_sql
from .report_writer import write_excel_report
from .summary_builder import build_scan_summary
from .sql_writer import write_schema_sql
from .csv_validator import validate_csv_export
from .readiness_score import calculate_migration_readiness_score
from .convertability import evaluate_table_convertability
from .duplicate_detector import build_duplicate_key_issue_rows
from .mysql_import_writer import write_mysql_import_sql
from .json_writer import write_scan_json

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



def build_readiness_details_table(tables, warnings) -> Table:
    readiness = calculate_migration_readiness_score(tables, warnings)

    details = Table(title="Migration readiness factors")
    details.add_column("Factor")
    details.add_column("Impact", justify="right")
    details.add_column("Severity")
    details.add_column("Message")
    details.add_column("Recommendation")

    details.add_row(
        "Overall readiness",
        f"{readiness.score} / 100",
        readiness.level,
        readiness.summary,
        "Use this score as a conservative planning indicator, not as automatic migration approval.",
    )

    if readiness.factors:
        for factor in readiness.factors:
            details.add_row(
                factor.name,
                str(factor.impact),
                factor.severity,
                factor.message,
                factor.recommendation,
            )
    else:
        details.add_row(
            "No major readiness penalties",
            "0",
            "Info",
            "No major readiness penalties were detected by the current heuristic model.",
            "Continue normal migration review before production use.",
        )

    return details


_CONVERTABILITY_STATUS_ORDER = {
    "Blocked": 0,
    "Exclude": 1,
    "Review": 2,
    "Ready": 3,
}


def build_convertability_detail_rows(tables, status_filter: str | None = None) -> list[dict[str, str]]:
    rows = []

    for table in tables:
        convertability = evaluate_table_convertability(table)
        rows.append(
            {
                "Table": table.table_name,
                "Status": convertability.status,
                "Reason": convertability.reason,
                "Rows": str(table.row_count or 0),
                "PK Status": table.primary_key_source,
            }
        )

    if status_filter is not None:
        normalized_status_filter = status_filter.strip().lower()
        rows = [row for row in rows if row["Status"].lower() == normalized_status_filter]

    return sorted(
        rows,
        key=lambda row: (
            _CONVERTABILITY_STATUS_ORDER.get(row["Status"], 99),
            row["Table"].lower(),
        ),
    )


def build_convertability_details_table(
    tables,
    limit: int | None = None,
    status_filter: str | None = None,
) -> Table:
    details = Table(title="Table convertability details")
    details.add_column("Table")
    details.add_column("Status")
    details.add_column("Reason")
    details.add_column("Rows", justify="right")
    details.add_column("PK Status")

    rows = build_convertability_detail_rows(tables, status_filter=status_filter)
    visible_rows = rows[:limit] if limit is not None else rows

    for row in visible_rows:
        details.add_row(
            row["Table"],
            row["Status"],
            row["Reason"],
            row["Rows"],
            row["PK Status"],
        )

    return details


def build_duplicate_key_detail_rows(tables) -> list[dict[str, str]]:
    rows = []

    for row in build_duplicate_key_issue_rows(tables):
        rows.append(
            {
                "Table": str(row["Table"] or ""),
                "Column": str(row["Column"] or ""),
                "Key Source": str(row["Key Source"] or ""),
                "Duplicate Values": str(row["Duplicate Values"] or 0),
                "Affected Rows": str(row["Affected Rows"] or 0),
                "Sample Values": str(row["Sample Values"] or ""),
            }
        )

    return sorted(
        rows,
        key=lambda row: (
            -int(row["Affected Rows"] or 0),
            row["Table"].lower(),
            row["Column"].lower(),
        ),
    )


def build_duplicate_key_details_table(tables) -> Table:
    details = Table(title="Duplicate key value details")
    details.add_column("Table")
    details.add_column("Column")
    details.add_column("Key Source")
    details.add_column("Duplicate Values", justify="right")
    details.add_column("Affected Rows", justify="right")
    details.add_column("Sample Values")

    rows = build_duplicate_key_detail_rows(tables)

    for row in rows:
        details.add_row(
            row["Table"],
            row["Column"],
            row["Key Source"],
            row["Duplicate Values"],
            row["Affected Rows"],
            row["Sample Values"],
        )

    return details


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
    fk_suggestions_out: Optional[Path] = typer.Option(
        None,
        "--fk-suggestions-out",
        help="Write review-only FK suggestions as SQL comments to the selected file. Works with normal scan and --summary-only.",
    ),
    json_out: Optional[Path] = typer.Option(
        None,
        "--json-out",
        help="Write structured JSON scan result to the selected file. Works with normal scan and --summary-only.",
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
        help="Only print scan summary; skip Excel report and schema generation. Other explicit outputs, such as --fk-suggestions-out or --json-out, are still created.",
    ),
    driver: str = typer.Option(DEFAULT_ACCESS_DRIVER, "--driver", help="ODBC driver name"),
    use_recommended_names: bool = typer.Option(
        False,
        "--use-recommended-names",
        help="Use normalized MySQL-safe table and column names in generated schema.sql.",
    ),
    readiness_details: bool = typer.Option(
        False,
        "--readiness-details",
        help="Print migration readiness factor details in the terminal.",
    ),
    duplicate_key_details: bool = typer.Option(
        False,
        "--duplicate-key-details",
        help="Print duplicate candidate/key value details in the terminal.",
    ),
    convertability_details: bool = typer.Option(
        False,
        "--convertability-details",
        help="Print table convertability status details in the terminal.",
    ),
    convertability_details_limit: Optional[int] = typer.Option(
        None,
        "--convertability-details-limit",
        min=1,
        help="Limit the number of rows shown by --convertability-details.",
    ),
    convertability_status: Optional[str] = typer.Option(
        None,
        "--convertability-status",
        help="Filter --convertability-details by status: Ready, Review, Exclude, or Blocked.",
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

    if convertability_status is not None:
        valid_convertability_statuses = {"ready", "review", "exclude", "blocked"}
        if convertability_status.strip().lower() not in valid_convertability_statuses:
            console.print(
                "[bold red]Error:[/bold red] --convertability-status must be one of: "
                "Ready, Review, Exclude, Blocked"
            )
            raise typer.Exit(code=1)

    if summary_only:
        console.print("[yellow]Summary-only mode: Excel report and schema SQL generation skipped.[/yellow]")
        if fk_suggestions_out is not None:
            console.print("[cyan]Explicit FK suggestions output requested; it will still be created.[/cyan]")
    else:
        report_path = write_excel_report(tables, warnings, out, database_path=database)
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

    if fk_suggestions_out is not None:
        fk_suggestions_path = write_fk_suggestions_sql(tables, fk_suggestions_out)
        console.print(f"[green]FK suggestions SQL comments created:[/green] {fk_suggestions_path}")

    if json_out is not None:
        json_path = write_scan_json(tables, warnings, json_out, database_path=database)
        console.print(f"[green]JSON scan result created:[/green] {json_path}")

    summary = Table(title="Scan summary")
    summary.add_column("Metric")
    summary.add_column("Value", justify="right")

    for row in build_scan_summary(tables, warnings, database_path=database):
        summary.add_row(str(row["Metric"]), str(row["Value"]))

    console.print(summary)

    if readiness_details:
        console.print(build_readiness_details_table(tables, warnings))

    if duplicate_key_details:
        duplicate_key_rows = build_duplicate_key_detail_rows(tables)

        if duplicate_key_rows:
            console.print(build_duplicate_key_details_table(tables))
        else:
            console.print("[green]No duplicate values detected in candidate/key columns.[/green]")

    if convertability_details:
        convertability_rows = build_convertability_detail_rows(
            tables,
            status_filter=convertability_status,
        )
        console.print(
            build_convertability_details_table(
                tables,
                limit=convertability_details_limit,
                status_filter=convertability_status,
            )
        )

        if convertability_details_limit is not None and len(convertability_rows) > convertability_details_limit:
            console.print(
                f"[yellow]Showing {convertability_details_limit} of {len(convertability_rows)} tables. "
                "Open the Excel Migration Plan sheet for full details.[/yellow]"
            )


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
    manifest_only: bool = typer.Option(
        False,
        "--manifest-only",
        help="Create only _export_manifest.csv without exporting table CSV files.",
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

    if manifest_only:
        console.print("[cyan]Manifest-only mode:[/cyan] CSV files will not be created.")

    try:
        results = export_access_tables_to_csv(
            database_path=database,
            output_dir=output_dir,
            driver=driver,
            use_recommended_names=use_recommended_names,
            table_filter=table_filter,
            skip_empty=skip_empty,
            limit=limit,
            manifest_only=manifest_only,
        )
    except AccessConnectionError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    ok_count = sum(1 for item in results if item["status"] == "ok")
    error_count = sum(1 for item in results if item["status"] == "error")
    total_rows = sum(item["row_count"] or 0 for item in results)

    skipped_empty_count = sum(1 for item in results if item["status"] == "skipped_empty")

    planned_count = sum(1 for item in results if item["status"] == "planned")

    if table_filter and not results:
        console.print("[yellow]No matching tables found for the provided --tables filter.[/yellow]")

    table = Table(title="CSV export summary")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Tables exported", str(ok_count))
    table.add_row("Tables planned", str(planned_count))
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

@app.command("validate-csv")
def validate_csv(
    export_dir: Path = typer.Argument(..., help="Directory containing _export_manifest.csv and exported CSV files."),
) -> None:
    """Validate a CSV export folder against its manifest."""
    console.print(f"[bold]LegacyDB Doctor[/bold] validating CSV export: {export_dir}")

    results = validate_csv_export(export_dir)

    ok_count = sum(1 for item in results if item["level"] == "ok")
    warning_count = sum(1 for item in results if item["level"] == "warning")
    error_count = sum(1 for item in results if item["level"] == "error")

    summary = Table(title="CSV validation summary")
    summary.add_column("Metric")
    summary.add_column("Value", justify="right")
    summary.add_row("OK", str(ok_count))
    summary.add_row("Warnings", str(warning_count))
    summary.add_row("Errors", str(error_count))
    summary.add_row("Checked items", str(len(results)))
    console.print(summary)

    if warning_count or error_count:
        details = Table(title="CSV validation details")
        details.add_column("Level")
        details.add_column("Table")
        details.add_column("Message")

        for item in results:
            if item["level"] in {"warning", "error"}:
                details.add_row(
                    str(item["level"]),
                    str(item.get("table") or ""),
                    str(item["message"]),
                )

        console.print(details)

    if error_count:
        raise typer.Exit(code=1)


@app.command("generate-import-sql")
def generate_import_sql(
    export_dir: Path = typer.Argument(..., help="Directory containing _export_manifest.csv and exported CSV files."),
    out: Path = typer.Option(..., "--out", "-o", help="Output path for review-only MySQL LOAD DATA import script."),
    use_recommended_names: bool = typer.Option(
        False,
        "--use-recommended-names",
        help="Use normalized MySQL-safe table names in generated import statements.",
    ),
) -> None:
    """Generate a review-only MySQL LOAD DATA import script from a CSV export manifest."""
    console.print(f"[bold]LegacyDB Doctor[/bold] generating MySQL import SQL from: {export_dir}")

    try:
        import_sql_path = write_mysql_import_sql(
            export_dir=export_dir,
            output_path=out,
            use_recommended_names=use_recommended_names,
        )
    except FileNotFoundError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]MySQL import SQL created:[/green] {import_sql_path}")
    console.print("[yellow]Review before running. The script uses LOAD DATA LOCAL INFILE.[/yellow]")


@app.command("drivers")
def list_drivers() -> None:
    """List installed ODBC drivers."""
    import pyodbc

    table = Table(title="Installed ODBC drivers")
    table.add_column("Driver")
    for item in pyodbc.drivers():
        table.add_row(item)
    console.print(table)
