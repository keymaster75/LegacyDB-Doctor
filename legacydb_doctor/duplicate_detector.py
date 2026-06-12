from __future__ import annotations

from .models import DuplicateKeyIssue, TableInfo


def count_duplicate_key_issues(tables: list[TableInfo]) -> int:
    return sum(len(table.duplicate_key_issues) for table in tables)


def count_duplicate_key_affected_rows(tables: list[TableInfo]) -> int:
    return sum(
        issue.affected_rows
        for table in tables
        for issue in table.duplicate_key_issues
    )


def build_duplicate_key_issue_rows(tables: list[TableInfo]) -> list[dict]:
    rows: list[dict] = []

    for table in tables:
        for issue in table.duplicate_key_issues:
            rows.append(
                {
                    "Severity": issue.severity,
                    "Table": issue.table_name,
                    "Column": issue.column_name,
                    "Key Source": issue.key_source,
                    "Duplicate Values": issue.duplicate_value_count,
                    "Affected Rows": issue.affected_rows,
                    "Sample Values": ", ".join(issue.sample_values),
                    "Recommendation": issue.recommendation,
                }
            )

    return rows
