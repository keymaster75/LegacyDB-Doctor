from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .access_reader import guess_potential_relationships
from .convertability import evaluate_table_convertability
from .duplicate_detector import build_duplicate_key_issue_rows
from .migration_checklist import build_migration_checklist_rows
from .models import ColumnInfo, DuplicateKeyIssue, TableInfo, WarningInfo
from .readiness_score import calculate_migration_readiness_score
from .report_writer import build_readiness_factors_rows
from .summary_builder import build_data_quality_rows, build_scan_summary


def _json_default(value: Any) -> Any:
    """JSON fallback for dataclasses, pathlib paths, and datetime-like objects."""
    if is_dataclass(value):
        return asdict(value)

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")

    return str(value)


def _summary_rows_to_dict(summary_rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}

    for row in summary_rows:
        metric = str(row.get("Metric", "")).strip()
        value = row.get("Value")
        if metric:
            summary[metric] = value

    return summary


def _database_metadata(database_path: str | Path | None) -> dict[str, Any]:
    if database_path is None:
        return {}

    database = Path(database_path)

    metadata: dict[str, Any] = {
        "file": str(database),
        "name": database.name,
    }

    try:
        metadata["size_mb"] = round(database.stat().st_size / (1024 * 1024), 2)
    except OSError:
        metadata["size_mb"] = None

    return metadata


def _column_to_dict(column: ColumnInfo) -> dict[str, Any]:
    return {
        "table_name": column.table_name,
        "column_name": column.column_name,
        "ordinal_position": column.ordinal_position,
        "type_name": column.type_name,
        "data_type": column.data_type,
        "column_size": column.column_size,
        "decimal_digits": column.decimal_digits,
        "nullable": column.nullable,
        "mysql_type": column.mysql_type,
        "empty_count": column.empty_count,
        "filled_count": column.filled_count,
        "fill_rate_percent": column.fill_rate_percent,
    }


def _duplicate_issue_to_dict(issue: DuplicateKeyIssue) -> dict[str, Any]:
    return {
        "table_name": issue.table_name,
        "column_name": issue.column_name,
        "key_source": issue.key_source,
        "duplicate_value_count": issue.duplicate_value_count,
        "affected_rows": issue.affected_rows,
        "sample_values": issue.sample_values,
        "severity": issue.severity,
        "recommendation": issue.recommendation,
    }


def _table_to_dict(table: TableInfo) -> dict[str, Any]:
    convertability = evaluate_table_convertability(table)

    return {
        "table_name": table.table_name,
        "row_count": table.row_count,
        "primary_keys": table.primary_keys,
        "primary_key_source": table.primary_key_source,
        "convertability_status": convertability.status,
        "convertability_reason": convertability.reason,
        "columns": [_column_to_dict(column) for column in table.columns],
        "duplicate_key_issues": [
            _duplicate_issue_to_dict(issue)
            for issue in table.duplicate_key_issues
        ],
    }


def _warning_to_dict(warning: WarningInfo) -> dict[str, Any]:
    return {
        "level": warning.level,
        "table_name": warning.table_name,
        "column_name": warning.column_name,
        "message": warning.message,
    }


def build_scan_json_payload(
    tables: list[TableInfo],
    warnings: list[WarningInfo],
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a structured JSON-serializable scan result payload.

    This payload is intended for future GUI, batch processing, comparison reports,
    HTML reports, and Pro/workflow layers. It does not replace the Excel report.
    """
    summary_rows = build_scan_summary(tables, warnings, database_path=database_path)
    readiness = calculate_migration_readiness_score(tables, warnings)
    potential_relationships = guess_potential_relationships(tables)

    return {
        "format": "legacydb-doctor-scan-result",
        "format_version": 1,
        "database": _database_metadata(database_path),
        "summary": _summary_rows_to_dict(summary_rows),
        "readiness": {
            "score": readiness.score,
            "level": readiness.level,
            "summary": readiness.summary,
            "factors": build_readiness_factors_rows(tables, warnings),
        },
        "tables": [_table_to_dict(table) for table in tables],
        "warnings": [_warning_to_dict(warning) for warning in warnings],
        "data_quality": build_data_quality_rows(tables),
        "duplicate_key_values": build_duplicate_key_issue_rows(tables),
        "potential_relationships": [
            {
                "child_table": relationship.child_table,
                "child_column": relationship.child_column,
                "parent_table": relationship.parent_table,
                "parent_column": relationship.parent_column,
                "confidence": relationship.confidence,
                "reason": relationship.reason,
            }
            for relationship in potential_relationships
        ],
        "migration_checklist": build_migration_checklist_rows(tables, warnings),
    }


def write_scan_json(
    tables: list[TableInfo],
    warnings: list[WarningInfo],
    output_path: str | Path,
    database_path: str | Path | None = None,
) -> Path:
    """Write structured scan output as UTF-8 JSON."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    payload = build_scan_json_payload(
        tables=tables,
        warnings=warnings,
        database_path=database_path,
    )

    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default),
        encoding="utf-8",
    )

    return output
