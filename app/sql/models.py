from dataclasses import dataclass, field


@dataclass(frozen=True)
class SQLColumn:
    table: str
    column: str
    alias: str | None = None


@dataclass(frozen=True)
class SQLJoin:
    left_table: str
    left_column: str
    right_table: str
    right_column: str
    join_type: str = "INNER"


@dataclass(frozen=True)
class SQLFilter:
    table: str
    column: str
    operator: str
    value: str


@dataclass(frozen=True)
class SQLAggregation:
    function: str
    table: str
    column: str
    alias: str | None = None


@dataclass(frozen=True)
class SQLOrder:
    expression: str
    direction: str


@dataclass(frozen=True)
class SQLQuery:
    select_columns: list[SQLColumn] = field(
        default_factory=list
    )
    joins: list[SQLJoin] = field(
        default_factory=list
    )
    filters: list[SQLFilter] = field(
        default_factory=list
    )
    aggregations: list[SQLAggregation] = field(
        default_factory=list
    )
    group_by: list[SQLColumn] = field(
        default_factory=list
    )
    order_by: list[SQLOrder] = field(
        default_factory=list
    )
    limit: int | None = None


@dataclass(frozen=True)
class CompiledSQL:
    sql: str
    parameters: dict[str, str]