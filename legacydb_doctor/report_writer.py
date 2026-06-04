from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from .models import TableInfo, WarningInfo


def _autosize_worksheet(ws) -> None:
    for column_cells in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column_cells[0].column)
        for cell in column_cells:
            value = "" if cell.value is None else str(cell.value)
            max_length = max(max_length, len(value))
        ws.column_dimensions[column_letter].width = min(max(max_length + 2, 12), 60)


def _style_worksheet(ws) -> None:
    header_fill = PatternFill("solid", fgColor="D9EAF7")
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
    ws.freeze_panes = "A2"
    _autosize_worksheet(ws)


def build_report_frames(tables: list[TableInfo], warnings: list[WarningInfo]) -> dict[str, pd.DataFrame]:
    total_rows = sum(t.row_count or 0 for t in tables)
    total_columns = sum(len(t.columns) for t in tables)

    summary_df = pd.DataFrame(
        [
            {"Metric": "Tables", "Value": len(tables)},
            {"Metric": "Columns", "Value": total_columns},
            {"Metric": "Rows", "Value": total_rows},
            {"Metric": "Warnings", "Value": len(warnings)},
        ]
    )

    tables_df = pd.DataFrame(
        [
            {
                "Table": table.table_name,
                "Rows": table.row_count,
                "Columns": len(table.columns),
            }
            for table in tables
        ]
    )

    columns_df = pd.DataFrame(
        [
            {
                "Table": column.table_name,
                "Column": column.column_name,
                "Ordinal": column.ordinal_position,
                "Access/ODBC Type": column.type_name,
                "ODBC Data Type": column.data_type,
                "Size": column.column_size,
                "Decimal Digits": column.decimal_digits,
                "Nullable": column.nullable,
                "Suggested MySQL Type": column.mysql_type,
            }
            for table in tables
            for column in table.columns
        ]
    )

    type_mapping_df = columns_df[["Access/ODBC Type", "Suggested MySQL Type"]].drop_duplicates() if not columns_df.empty else pd.DataFrame(columns=["Access/ODBC Type", "Suggested MySQL Type"])

    warnings_df = pd.DataFrame(
        [
            {
                "Level": warning.level,
                "Table": warning.table_name,
                "Column": warning.column_name,
                "Message": warning.message,
            }
            for warning in warnings
        ]
    )
    if warnings_df.empty:
        warnings_df = pd.DataFrame([{"Level": "info", "Table": None, "Column": None, "Message": "No warnings generated in this starter scan."}])

    return {
        "Summary": summary_df,
        "Tables": tables_df,
        "Columns": columns_df,
        "Type Mapping": type_mapping_df,
        "Warnings": warnings_df,
    }


def write_excel_report(tables: list[TableInfo], warnings: list[WarningInfo], output_path: str | Path) -> Path:
    output = Path(output_path)
    frames = build_report_frames(tables, warnings)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in frames.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

        workbook = writer.book
        for ws in workbook.worksheets:
            _style_worksheet(ws)

    return output
