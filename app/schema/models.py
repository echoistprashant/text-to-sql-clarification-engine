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


@dataclass(frozen=True)
class ColumnValueProfile:
    table_name: str
    column_name: str
    values: list[str]


@dataclass(frozen=True)
class ValueMatch:
    table_name: str
    column_name: str
    value: str


@dataclass(frozen=True)
class RankedTable:
    table_name: str
    score: int



@dataclass(frozen=True)
class SchemaRetrievalResult:
    tables: list[str]
    value_matches: list[ValueMatch]
    ranked_tables: list[RankedTable]
    join_path: list[str]    