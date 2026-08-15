import json

from app.intent.models import (
    Aggregation,
    IntentFilter,
    QueryIntent,
    SortDirection,
)


def parse_intent_response(response: str) -> QueryIntent:
    data = json.loads(response)

    filters = [
        IntentFilter(
            column=item["column"],
            operator=item["operator"],
            value=item["value"],
        )
        for item in data.get("filters", [])
    ]

    aggregation = data.get("aggregation")
    if aggregation is not None:
        aggregation = Aggregation(aggregation)

    sort_direction = data.get("sort_direction")
    if sort_direction is not None:
        sort_direction = SortDirection(sort_direction)

    return QueryIntent(
        entity=data.get("entity"),
        filters=filters,
        metric=data.get("metric"),
        aggregation=aggregation,
        sort_direction=sort_direction,
        limit=data.get("limit"),
    )