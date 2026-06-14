from __future__ import annotations

from .access_reader import guess_potential_relationships
from .models import TableInfo, WarningInfo
from .readiness_score import calculate_migration_readiness_score
from .duplicate_detector import count_duplicate_key_affected_rows, count_duplicate_key_issues


def _status_for_readiness_level(level: str) -> str:
    if level == "High":
        return "OK"
    if level == "Medium":
        return "Warning"
    return "Fail"


def _count_data_quality_issues(tables: list[TableInfo]) -> tuple[int, int, int]:
    high = 0
    medium = 0
    low = 0

    for table in tables:
        for column in table.columns:
            if column.fill_rate_percent is None:
                continue

            if column.fill_rate_percent == 0:
                high += 1
            elif column.fill_rate_percent < 10:
                medium += 1
            elif column.fill_rate_percent < 50:
                low += 1

    return high, medium, low


def _looks_like_artifact_table(table_name: str) -> bool:
    name = table_name.lower()
    markers = [
        "importerrors",
        "import errors",
        "copy of",
        "copy2 of",
        "kopija",
        "backup",
        "_bak",
        " bak",
        "temp",
        "tmp",
        "test",
        "staro",
        "old",
    ]
    return any(marker in name for marker in markers)


def build_migration_checklist_rows(tables: list[TableInfo], warnings: list[WarningInfo]) -> list[dict]:
    """Build a high-level migration action checklist."""
    readiness = calculate_migration_readiness_score(tables, warnings)
    potential_relationships = guess_potential_relationships(tables)

    table_count = len(tables)
    pk_none_count = sum(1 for table in tables if table.primary_key_source == "none")
    warning_count = sum(1 for warning in warnings if warning.level == "warning")
    dq_high_count, dq_medium_count, dq_low_count = _count_data_quality_issues(tables)
    cleanup_candidate_count = sum(
        1
        for table in tables
        if table.row_count == 0
        or table.primary_key_source == "none"
        or _looks_like_artifact_table(table.table_name)
    )
    duplicate_key_issue_count = count_duplicate_key_issues(tables)
    duplicate_key_affected_rows = count_duplicate_key_affected_rows(tables)

    rows = [
        {
            "Area": "Readiness score",
            "Status": _status_for_readiness_level(readiness.level),
            "Finding": f"Migration readiness score is {readiness.score} / 100 ({readiness.level}).",
            "Recommended Action": "Review readiness factors before starting migration.",
            "Related Sheet": "Readiness Factors",
        }
    ]

    if pk_none_count:
        rows.append(
            {
                "Area": "Primary keys",
                "Status": "Fail",
                "Finding": f"{pk_none_count} of {table_count} tables have no detected primary key or unique index.",
                "Recommended Action": "Review or define stable keys before migration.",
                "Related Sheet": "Primary Keys",
            }
        )
    else:
        rows.append(
            {
                "Area": "Primary keys",
                "Status": "OK",
                "Finding": "All tables have a detected primary key or unique index.",
                "Recommended Action": "Review key assumptions before production migration.",
                "Related Sheet": "Primary Keys",
            }
        )

    if dq_high_count or dq_medium_count:
        rows.append(
            {
                "Area": "Data quality",
                "Status": "Fail" if dq_high_count else "Warning",
                "Finding": f"{dq_high_count} completely empty columns and {dq_medium_count} almost empty columns detected.",
                "Recommended Action": "Review empty and low-fill columns before migration.",
                "Related Sheet": "Data Quality",
            }
        )
    elif dq_low_count:
        rows.append(
            {
                "Area": "Data quality",
                "Status": "Warning",
                "Finding": f"{dq_low_count} low-fill columns detected.",
                "Recommended Action": "Confirm whether low fill rate is expected.",
                "Related Sheet": "Data Quality",
            }
        )
    else:
        rows.append(
            {
                "Area": "Data quality",
                "Status": "OK",
                "Finding": "No low-fill data quality issues detected by the current checks.",
                "Recommended Action": "Continue normal data validation before production migration.",
                "Related Sheet": "Data Quality",
            }
        )

    if cleanup_candidate_count:
        rows.append(
            {
                "Area": "Cleanup",
                "Status": "Warning",
                "Finding": f"{cleanup_candidate_count} tables may require cleanup or structural review.",
                "Recommended Action": "Review cleanup candidates and exclude non-production artifacts.",
                "Related Sheet": "Cleanup Candidates",
            }
        )
    else:
        rows.append(
            {
                "Area": "Cleanup",
                "Status": "OK",
                "Finding": "No cleanup candidates detected by current rules.",
                "Recommended Action": "Continue normal application-owner review.",
                "Related Sheet": "Cleanup Candidates",
            }
        )

    if duplicate_key_issue_count:
        rows.append(
            {
                "Area": "Duplicate key values",
                "Status": "Fail",
                "Finding": (
                    f"{duplicate_key_issue_count} candidate/key-like columns contain duplicate values "
                    f"affecting {duplicate_key_affected_rows} rows."
                ),
                "Recommended Action": "Clean duplicate values before creating unique keys or importing to MySQL.",
                "Related Sheet": "Duplicate Key Values",
            }
        )
    else:
        rows.append(
            {
                "Area": "Duplicate key values",
                "Status": "OK",
                "Finding": "No duplicate values detected in candidate/key-like columns.",
                "Recommended Action": "Continue normal key validation before production migration.",
                "Related Sheet": "Duplicate Key Values",
            }
        )

    if potential_relationships:
        rows.append(
            {
                "Area": "Relationships",
                "Status": "Warning",
                "Finding": f"{len(potential_relationships)} potential relationships detected heuristically.",
                "Recommended Action": "Confirm relationships manually before creating real foreign keys.",
                "Related Sheet": "Potential Relationships",
            }
        )
        rows.append(
            {
                "Area": "FK suggestions",
                "Status": "Info",
                "Finding": "Review-only foreign key suggestions are available.",
                "Recommended Action": "Use FK suggestions as developer guidance, not as automatic DDL.",
                "Related Sheet": "FK Suggestions",
            }
        )
    else:
        rows.append(
            {
                "Area": "Relationships",
                "Status": "Warning" if table_count > 1 else "OK",
                "Finding": "No potential relationships detected.",
                "Recommended Action": "Review relationship design manually if the database is relational.",
                "Related Sheet": "Potential Relationships",
            }
        )

    if warning_count:
        rows.append(
            {
                "Area": "Warnings",
                "Status": "Warning",
                "Finding": f"{warning_count} warning notes were generated during scan.",
                "Recommended Action": "Review warnings before migration.",
                "Related Sheet": "Warnings",
            }
        )
    else:
        rows.append(
            {
                "Area": "Warnings",
                "Status": "OK",
                "Finding": "No warning notes were generated during scan.",
                "Recommended Action": "Continue normal review.",
                "Related Sheet": "Warnings",
            }
        )

    rows.append(
        {
            "Area": "CSV export readiness",
            "Status": "Info",
            "Finding": "CSV export with manifest and validation is available.",
            "Recommended Action": "Use export-csv and validate-csv before importing data into MySQL.",
            "Related Sheet": "_export_manifest.csv / validate-csv",
        }
    )

    rows.append(
        {
            "Area": "Schema",
            "Status": "Info",
            "Finding": "Starter MySQL schema can be generated for review.",
            "Recommended Action": "Review generated schema before running it in production.",
            "Related Sheet": "schema.sql",
        }
    )

    return rows
