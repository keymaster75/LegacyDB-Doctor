from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _html_table(headers: list[str], rows: list[list[Any]]) -> str:
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)

    if not rows:
        body_html = f'<tr><td colspan="{len(headers)}">No data.</td></tr>'
    else:
        body_html = ""
        for row in rows:
            cells = "".join(f"<td>{escape(_as_text(value))}</td>" for value in row)
            body_html += f"<tr>{cells}</tr>\n"

    return f"""
<table>
  <thead>
    <tr>{header_html}</tr>
  </thead>
  <tbody>
    {body_html}
  </tbody>
</table>
""".strip()


def _summary_rows(summary: dict[str, Any]) -> list[list[Any]]:
    key_metrics = [
        "Tables",
        "Columns",
        "Rows",
        "Warnings",
        "Info",
        "Total notes",
        "Migration readiness score",
        "Migration readiness level",
        "Convertability ready",
        "Convertability review",
        "Convertability exclude",
        "Convertability blocked",
        "Duplicate key issues",
        "Duplicate key affected rows",
        "PK formal",
        "PK unique_index",
        "PK candidate",
        "PK none",
        "DQ high",
        "DQ medium",
        "DQ low",
        "Potential relationships",
    ]

    return [[metric, summary.get(metric, "")] for metric in key_metrics if metric in summary]


def _table_status_rows(tables: list[dict[str, Any]]) -> list[list[Any]]:
    rows = []

    for table in tables:
        rows.append(
            [
                table.get("table_name"),
                table.get("convertability_status"),
                table.get("row_count"),
                table.get("primary_key_source"),
                table.get("convertability_reason"),
            ]
        )

    status_order = {"Blocked": 0, "Exclude": 1, "Review": 2, "Ready": 3}
    return sorted(
        rows,
        key=lambda row: (
            status_order.get(_as_text(row[1]), 99),
            _as_text(row[0]).lower(),
        ),
    )


def _duplicate_rows(duplicate_key_values: list[dict[str, Any]]) -> list[list[Any]]:
    rows = []

    for item in duplicate_key_values:
        table = item.get("Table")
        if not table:
            continue

        rows.append(
            [
                item.get("Severity"),
                item.get("Table"),
                item.get("Column"),
                item.get("Key Source"),
                item.get("Duplicate Values"),
                item.get("Affected Rows"),
                item.get("Sample Values"),
                item.get("Recommendation"),
            ]
        )

    return rows


def _warning_rows(warnings: list[dict[str, Any]]) -> list[list[Any]]:
    return [
        [
            item.get("level"),
            item.get("table_name"),
            item.get("column_name"),
            item.get("message"),
        ]
        for item in warnings
    ]


def build_html_report(payload: dict[str, Any]) -> str:
    """Build a simple standalone HTML report from a LegacyDB Doctor JSON payload."""
    database = payload.get("database", {}) or {}
    summary = payload.get("summary", {}) or {}
    readiness = payload.get("readiness", {}) or {}
    tables = payload.get("tables", []) or []
    duplicate_key_values = payload.get("duplicate_key_values", []) or []
    warnings = payload.get("warnings", []) or []

    title = f"LegacyDB Doctor Report - {database.get('name') or 'Scan result'}"

    summary_table = _html_table(["Metric", "Value"], _summary_rows(summary))
    table_status_table = _html_table(
        ["Table", "Status", "Rows", "PK Status", "Reason"],
        _table_status_rows(tables),
    )
    duplicate_table = _html_table(
        [
            "Severity",
            "Table",
            "Column",
            "Key Source",
            "Duplicate Values",
            "Affected Rows",
            "Sample Values",
            "Recommendation",
        ],
        _duplicate_rows(duplicate_key_values),
    )
    warnings_table = _html_table(
        ["Level", "Table", "Column", "Message"],
        _warning_rows(warnings),
    )

    readiness_score = readiness.get("score", "")
    readiness_level = readiness.get("level", "")
    readiness_summary = readiness.get("summary", "")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(title)}</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 32px;
      color: #222;
      line-height: 1.4;
    }}
    h1, h2 {{
      color: #1f2937;
    }}
    .meta, .note {{
      color: #555;
    }}
    .score-card {{
      border: 1px solid #d1d5db;
      border-radius: 8px;
      padding: 16px;
      margin: 16px 0 24px 0;
      background: #f9fafb;
    }}
    .score {{
      font-size: 28px;
      font-weight: bold;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      margin: 12px 0 28px 0;
      font-size: 14px;
    }}
    th, td {{
      border: 1px solid #d1d5db;
      padding: 8px;
      vertical-align: top;
    }}
    th {{
      background: #eef2f7;
      text-align: left;
    }}
    footer {{
      margin-top: 40px;
      font-size: 12px;
      color: #666;
    }}
  </style>
</head>
<body>
  <h1>LegacyDB Doctor HTML Report</h1>

  <p class="meta">
    <strong>Database:</strong> {escape(_as_text(database.get("name")))}<br>
    <strong>File:</strong> {escape(_as_text(database.get("file")))}<br>
    <strong>Scan timestamp:</strong> {escape(_as_text(summary.get("Scan timestamp")))}
  </p>

  <div class="score-card">
    <div>Migration readiness</div>
    <div class="score">{escape(_as_text(readiness_score))} / 100 — {escape(_as_text(readiness_level))}</div>
    <p>{escape(_as_text(readiness_summary))}</p>
  </div>

  <h2>Summary</h2>
  {summary_table}

  <h2>Table Convertability</h2>
  {table_status_table}

  <h2>Duplicate Key Findings</h2>
  {duplicate_table}

  <h2>Warnings</h2>
  {warnings_table}

  <footer>
    Generated from LegacyDB Doctor structured JSON output. Review findings before production migration.
  </footer>
</body>
</html>
"""


def render_html_report_from_json(
    json_path: str | Path,
    output_path: str | Path,
) -> Path:
    """Read a LegacyDB Doctor JSON scan result and write a standalone HTML report."""
    source = Path(json_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    payload = json.loads(source.read_text(encoding="utf-8"))
    html = build_html_report(payload)

    output.write_text(html, encoding="utf-8")

    return output
