from dataclasses import dataclass, field
from enum import Enum


class Aggregation(str, Enum):
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass(frozen=True)
class IntentFilter:
    column: str
    operator: str
    value: str


@dataclass(frozen=True)
class QueryIntent:
    entity: str | None = None
    filters: list[IntentFilter] = field(default_factory=list)
    metric: str | None = None
    aggregation: Aggregation | None = None
    sort_direction: SortDirection | None = None
    limit: int | None = None