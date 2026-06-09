from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .access_reader import guess_potential_relationships, suggest_mysql_identifier
from .readiness_score import calculate_migration_readiness_score
from .models import TableInfo, WarningInfo


def build_data_quality_rows(tables: list[TableInfo]) -> list[dict]:
    data_quality_rows = []

    for table in tables:
        for column in table.columns:
            if column.fill_rate_percent is None:
                continue

            if column.fill_rate_percent == 0:
                issue = "Completely empty column"
                severity = "High"
                suggested_action = "Review if this column is still needed before migration."
            elif column.fill_rate_percent < 10:
                issue = "Almost empty column"
                severity = "Medium"
                suggested_action = "Review business meaning. Consider excluding or documenting this column."
            elif column.fill_rate_percent < 50:
                issue = "Low fill rate"
                severity = "Low"
                suggested_action = "Review whether low fill rate is expected."
            else:
                continue

            data_quality_rows.append(
                {
                    "Severity": severity,
                    "Table": table.table_name,
                    "Column": column.column_name,
                    "Recommended MySQL Table": suggest_mysql_identifier(table.table_name),
                    "Recommended MySQL Column": suggest_mysql_identifier(column.column_name),
                    "Rows": table.row_count,
                    "Empty Values": column.empty_count,
                    "Filled Values": column.filled_count,
                    "Fill Rate %": column.fill_rate_percent,
                    "Issue": issue,
                    "Suggested Action": suggested_action,
                }
            )

    return data_quality_rows


def build_scan_summary(
    tables: list[TableInfo],
    warnings: list[WarningInfo],
    database_path: str | Path | None = None,
) -> list[dict[str, int | str]]:
    warning_count = sum(1 for item in warnings if item.level == "warning")
    info_count = sum(1 for item in warnings if item.level == "info")

    pk_formal_count = sum(1 for table in tables if table.primary_key_source == "formal")
    pk_unique_index_count = sum(1 for table in tables if table.primary_key_source == "unique_index")
    pk_candidate_count = sum(1 for table in tables if table.primary_key_source == "candidate")
    pk_none_count = sum(1 for table in tables if table.primary_key_source == "none")

    data_quality_rows = build_data_quality_rows(tables)
    dq_high_count = sum(1 for item in data_quality_rows if item["Severity"] == "High")
    dq_medium_count = sum(1 for item in data_quality_rows if item["Severity"] == "Medium")
    dq_low_count = sum(1 for item in data_quality_rows if item["Severity"] == "Low")
    potential_relationships = guess_potential_relationships(tables)
    readiness_score = calculate_migration_readiness_score(tables, warnings)

    metadata_rows: list[dict[str, int | str]] = [
        {"Metric": "Scan timestamp", "Value": datetime.now().isoformat(timespec="seconds")}
    ]

    if database_path is not None:
        database = Path(database_path)
        metadata_rows.insert(0, {"Metric": "Database file", "Value": str(database)})
        metadata_rows.insert(1, {"Metric": "Database name", "Value": database.name})

        try:
            size_mb = database.stat().st_size / (1024 * 1024)
        except OSError:
            size_mb = None

        if size_mb is not None:
            metadata_rows.insert(2, {"Metric": "Database size MB", "Value": f"{size_mb:.2f}"})

    return metadata_rows + [
        {"Metric": "Tables", "Value": len(tables)},
        {"Metric": "Columns", "Value": sum(len(t.columns) for t in tables)},
        {"Metric": "Rows", "Value": sum(t.row_count or 0 for t in tables)},
        {"Metric": "Warnings", "Value": warning_count},
        {"Metric": "Info", "Value": info_count},
        {"Metric": "Total notes", "Value": len(warnings)},
        {"Metric": "Migration readiness score", "Value": f"{readiness_score.score} / 100"},
        {"Metric": "Migration readiness level", "Value": readiness_score.level},
        {"Metric": "PK formal", "Value": pk_formal_count},
        {"Metric": "PK unique_index", "Value": pk_unique_index_count},
        {"Metric": "PK candidate", "Value": pk_candidate_count},
        {"Metric": "PK none", "Value": pk_none_count},
        {"Metric": "DQ high", "Value": dq_high_count},
        {"Metric": "DQ medium", "Value": dq_medium_count},
        {"Metric": "DQ low", "Value": dq_low_count},
        {"Metric": "Potential relationships", "Value": len(potential_relationships)},
    ]