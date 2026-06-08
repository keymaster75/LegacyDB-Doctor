from __future__ import annotations

from dataclasses import dataclass

from .access_reader import guess_potential_relationships
from .models import TableInfo, WarningInfo


@dataclass(frozen=True)
class ReadinessFactor:
    name: str
    impact: int
    severity: str
    message: str
    recommendation: str


@dataclass(frozen=True)
class ReadinessScore:
    score: int
    level: str
    summary: str
    factors: list[ReadinessFactor]


def _score_level(score: int) -> str:
    if score >= 80:
        return "High"
    if score >= 50:
        return "Medium"
    return "Low"


def _score_summary(level: str) -> str:
    if level == "High":
        return "Database looks broadly ready for migration, with normal review still required."
    if level == "Medium":
        return "Database is partially ready for migration, but requires targeted review."
    return "Database needs significant review before migration."


def _is_artifact_table_name(table_name: str) -> bool:
    name = table_name.lower()

    artifact_markers = [
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

    return any(marker in name for marker in artifact_markers)


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


def _bounded_penalty(value: int, limit: int) -> int:
    return min(max(value, 0), limit)


def calculate_migration_readiness_score(
    tables: list[TableInfo],
    warnings: list[WarningInfo],
) -> ReadinessScore:
    """Calculate a conservative, explainable migration-readiness score.

    The score is intentionally heuristic. It is meant to support review and
    planning, not to automatically approve a migration.
    """
    factors: list[ReadinessFactor] = []

    table_count = len(tables)
    safe_table_count = max(table_count, 1)

    pk_none_count = sum(1 for table in tables if table.primary_key_source == "none")
    warning_count = sum(1 for item in warnings if item.level == "warning")
    dq_high_count, dq_medium_count, dq_low_count = _count_data_quality_issues(tables)
    artifact_table_count = sum(1 for table in tables if _is_artifact_table_name(table.table_name))
    empty_table_count = sum(1 for table in tables if table.row_count == 0)
    potential_relationship_count = len(guess_potential_relationships(tables))

    if pk_none_count:
        penalty = _bounded_penalty(round((pk_none_count / safe_table_count) * 35), 35)
        factors.append(
            ReadinessFactor(
                name="Tables without primary key or unique index",
                impact=-penalty,
                severity="High" if penalty >= 20 else "Medium",
                message=f"{pk_none_count} of {table_count} tables have no detected primary key or unique index.",
                recommendation="Review these tables and confirm or add stable keys before migration.",
            )
        )

    if artifact_table_count:
        penalty = _bounded_penalty(artifact_table_count * 5, 20)
        factors.append(
            ReadinessFactor(
                name="Possible cleanup/artifact tables",
                impact=-penalty,
                severity="High" if penalty >= 10 else "Medium",
                message=f"{artifact_table_count} tables look like import-error, copy, backup, temp, test, or old tables.",
                recommendation="Review these tables and exclude non-production artifacts from migration.",
            )
        )

    if dq_high_count:
        penalty = _bounded_penalty(dq_high_count * 2, 20)
        factors.append(
            ReadinessFactor(
                name="Completely empty columns",
                impact=-penalty,
                severity="High" if penalty >= 10 else "Medium",
                message=f"{dq_high_count} columns are completely empty.",
                recommendation="Review whether empty columns should be migrated, documented, or removed.",
            )
        )

    if dq_medium_count:
        penalty = _bounded_penalty(dq_medium_count, 10)
        factors.append(
            ReadinessFactor(
                name="Almost empty columns",
                impact=-penalty,
                severity="Medium",
                message=f"{dq_medium_count} columns have less than 10% filled values.",
                recommendation="Confirm business meaning before migration.",
            )
        )

    if warning_count:
        penalty = _bounded_penalty(warning_count * 2, 20)
        factors.append(
            ReadinessFactor(
                name="Migration warnings",
                impact=-penalty,
                severity="Medium" if penalty < 10 else "High",
                message=f"{warning_count} warning notes were generated during scan.",
                recommendation="Review warning notes before migration.",
            )
        )

    if empty_table_count:
        penalty = _bounded_penalty(empty_table_count, 5)
        factors.append(
            ReadinessFactor(
                name="Empty tables",
                impact=-penalty,
                severity="Low",
                message=f"{empty_table_count} tables are empty.",
                recommendation="Confirm whether empty tables are valid application/domain tables.",
            )
        )

    if table_count > 1 and potential_relationship_count == 0:
        factors.append(
            ReadinessFactor(
                name="No potential relationships detected",
                impact=-5,
                severity="Low",
                message="No potential relationships were detected between tables.",
                recommendation="Review relationship design manually if the database is relational.",
            )
        )

    score = 100 + sum(factor.impact for factor in factors)
    score = max(0, min(100, score))
    level = _score_level(score)

    return ReadinessScore(
        score=score,
        level=level,
        summary=_score_summary(level),
        factors=factors,
    )
