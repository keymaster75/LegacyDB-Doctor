from __future__ import annotations

from .models import TableInfo, WarningInfo
from .report_writer import build_data_quality_rows


def build_scan_summary(tables: list[TableInfo], warnings: list[WarningInfo]) -> list[dict[str, int | str]]:
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

    return [
        {"Metric": "Tables", "Value": len(tables)},
        {"Metric": "Columns", "Value": sum(len(t.columns) for t in tables)},
        {"Metric": "Rows", "Value": sum(t.row_count or 0 for t in tables)},
        {"Metric": "Warnings", "Value": warning_count},
        {"Metric": "Info", "Value": info_count},
        {"Metric": "Total notes", "Value": len(warnings)},
        {"Metric": "PK formal", "Value": pk_formal_count},
        {"Metric": "PK unique_index", "Value": pk_unique_index_count},
        {"Metric": "PK candidate", "Value": pk_candidate_count},
        {"Metric": "PK none", "Value": pk_none_count},
        {"Metric": "DQ high", "Value": dq_high_count},
        {"Metric": "DQ medium", "Value": dq_medium_count},
        {"Metric": "DQ low", "Value": dq_low_count},
    ]