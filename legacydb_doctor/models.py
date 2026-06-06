from dataclasses import dataclass, field
from typing import Any


@dataclass
class ColumnInfo:
    table_name: str
    column_name: str
    ordinal_position: int | None
    type_name: str | None
    data_type: Any | None
    column_size: int | None
    decimal_digits: int | None
    nullable: bool | None
    mysql_type: str | None = None
    empty_count: int | None = None
    filled_count: int | None = None
    fill_rate_percent: float | None = None


@dataclass
class TableInfo:
    table_name: str
    row_count: int | None = None
    columns: list[ColumnInfo] = field(default_factory=list)
    primary_keys: list[str] = field(default_factory=list)
    primary_key_source: str = "none"


@dataclass
class WarningInfo:
    level: str
    table_name: str | None
    column_name: str | None
    message: str


@dataclass
class RelationshipInfo:
    fk_name: str | None
    parent_table: str | None
    parent_column: str | None
    child_table: str | None
    child_column: str | None
    update_rule: str | None = None
    delete_rule: str | None = None

@dataclass
class PotentialRelationshipInfo:
    child_table: str
    child_column: str
    parent_table: str
    parent_column: str
    confidence: str
    reason: str