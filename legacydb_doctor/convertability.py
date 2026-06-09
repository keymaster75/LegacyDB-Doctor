from __future__ import annotations

from dataclasses import dataclass

from .models import TableInfo


@dataclass(frozen=True)
class ConvertabilityResult:
    status: str
    reason: str


def _artifact_reason(table_name: str) -> str | None:
    name = table_name.lower()

    if "importerrors" in name or "import errors" in name:
        return "Access import error table."
    if "copy of" in name or "copy2 of" in name or "kopija" in name:
        return "Backup/copy table."
    if "backup" in name or "_bak" in name or " bak" in name:
        return "Backup table."
    if "temp" in name or "tmp" in name:
        return "Temporary table."
    if "test" in name:
        return "Test table."
    if "staro" in name or "old" in name:
        return "Old/legacy copy table."

    return None


def evaluate_table_convertability(table: TableInfo) -> ConvertabilityResult:
    """Evaluate table-level migration convertability.

    This is a conservative planning status, not an automatic migration decision.
    """
    artifact_reason = _artifact_reason(table.table_name)
    if artifact_reason:
        return ConvertabilityResult(
            status="Exclude",
            reason=f"{artifact_reason} Exclude from migration unless confirmed as production data.",
        )

    row_count = table.row_count or 0
    has_rows = row_count > 0

    if table.primary_key_source == "none" and has_rows:
        return ConvertabilityResult(
            status="Blocked",
            reason="Table has rows but no detected primary key, unique index, or candidate key.",
        )

    if not has_rows:
        return ConvertabilityResult(
            status="Review",
            reason="Empty table. Confirm with application owner whether it is a valid domain/application table.",
        )

    if table.primary_key_source == "candidate":
        return ConvertabilityResult(
            status="Review",
            reason="Only a candidate key was detected. Confirm the key before migration.",
        )

    return ConvertabilityResult(
        status="Ready",
        reason="Table looks structurally ready for migration based on current checks.",
    )
