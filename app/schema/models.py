from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnSchema:
    name: str
    data_type: str
    nullable: bool


@dataclass(frozen=True)
class ForeignKeySchema:
    column: str
    references_table: str
    references_column: str


@dataclass(frozen=True)
class TableSchema:
    name: str
    columns: list[ColumnSchema]
    primary_key: list[str]
    foreign_keys: list[ForeignKeySchema]


@dataclass(frozen=True)
class DatabaseSchema:
    tables: list[TableSchema]