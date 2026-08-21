import json

from app.intent.models import (
    Aggregation,
    IntentFilter,
    QueryIntent,
    SortDirection,
)

_OPERATOR_ALIASES = {
    "eq": "=",
    "==": "=",
    "equals": "=",
    "equal": "=",
    "ne": "!=",
    "neq": "!=",
    "not_equal": "!=",
    "not_equals": "!=",
    "gt": ">",
    "greater_than": ">",
    "gte": ">=",
    "greater_than_or_equal": ">=",
    "lt": "<",
    "less_than": "<",
    "lte": "<=",
    "less_than_or_equal": "<=",
    "contains": "LIKE",
    "like": "LIKE",
}


def _normalize_operator(
    operator: object,
) -> str:
    if not isinstance(operator, str):
        raise TypeError(
            "Filter operator must be a string."
        )

    normalized = operator.strip().lower()

    if normalized in _OPERATOR_ALIASES:
        return _OPERATOR_ALIASES[normalized]

    allowed_operators = {
        "=",
        "!=",
        ">",
        ">=",
        "<",
        "<=",
        "LIKE",
    }

    if operator in allowed_operators:
        return operator

    raise ValueError(
        f"Unsupported filter operator: "
        f"{operator!r}."
    )


def _parse_filters(
    data: object,
) -> list[IntentFilter]:
    if data is None:
        return []

    if not isinstance(data, list):
        raise TypeError(
            "'filters' must be a list."
        )

    filters: list[IntentFilter] = []

    for item in data:
        if not isinstance(item, dict):
            raise TypeError(
                "Each filter must be an object."
            )

        required_fields = (
            "column",
            "operator",
            "value",
        )

        for field in required_fields:
            if field not in item:
                raise ValueError(
                    f"Filter is missing required field "
                    f"'{field}'."
                )

        filters.append(
            IntentFilter(
                column=item["column"],
                operator=_normalize_operator(
                    item["operator"]
                ),
                value=item["value"],
            )
        )

    return filters


def parse_intent_response(
    response: str,
) -> QueryIntent:
    try:
        data = json.loads(response)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "LLM response is not valid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise TypeError(
            "LLM intent response must be a JSON object."
        )

    filters = _parse_filters(
        data.get("filters", [])
    )

    aggregation = data.get("aggregation")

    if aggregation is not None:
        try:
            aggregation = Aggregation(aggregation)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported aggregation: "
                f"{aggregation!r}."
            ) from exc

    sort_direction = data.get("sort_direction")

    if sort_direction is not None:
        try:
            sort_direction = SortDirection(
                sort_direction
            )
        except ValueError as exc:
            raise ValueError(
                "Unsupported sort direction: "
                f"{sort_direction!r}."
            ) from exc

    limit = data.get("limit")

    if limit is not None:
        if isinstance(limit, bool) or not isinstance(
            limit,
            int,
        ):
            raise ValueError(
                "'limit' must be an integer or null."
            )

        if limit <= 0:
            raise ValueError(
                "'limit' must be greater than zero."
            )

    return QueryIntent(
        entity=data.get("entity"),
        filters=filters,
        metric=data.get("metric"),
        aggregation=aggregation,
        sort_direction=sort_direction,
        limit=limit,
    )