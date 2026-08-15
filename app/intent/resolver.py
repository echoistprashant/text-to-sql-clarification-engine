from app.intent.models import Aggregation, QueryIntent, SortDirection
from app.intent.state import ClarificationState


def resolve_clarification(
    state: ClarificationState,
    answer: str,
) -> QueryIntent:
    normalized_answer = answer.strip().lower()

    if state.clarification is None:
        raise ValueError("There is no pending clarification.")

    if state.clarification.field != "metric":
        raise ValueError(
            f"Unsupported clarification field: "
            f"{state.clarification.field}"
        )

    if normalized_answer in {
        "units_purchased",
        "most units purchased",
        "units",
        "quantity",
        "most units",
    }:
        return _resolve_units_purchased(state.intent)

    if normalized_answer in {
        "orders",
        "most orders",
        "number of orders",
        "order count",
    }:
        return _resolve_orders(state.intent)

    if normalized_answer in {
        "total_spending",
        "highest total spending",
        "total spending",
        "spending",
    }:
        return _resolve_total_spending(state.intent)

    raise ValueError(
        "Unsupported clarification answer. "
        "Expected units_purchased, orders, or total_spending."
    )


def _resolve_units_purchased(
    intent: QueryIntent,
) -> QueryIntent:
    return QueryIntent(
        entity=intent.entity,
        filters=intent.filters,
        metric="order_items.quantity",
        aggregation=Aggregation.SUM,
        sort_direction=intent.sort_direction or SortDirection.DESC,
        limit=intent.limit,
    )


def _resolve_orders(
    intent: QueryIntent,
) -> QueryIntent:
    return QueryIntent(
        entity=intent.entity,
        filters=intent.filters,
        metric="orders.id",
        aggregation=Aggregation.COUNT,
        sort_direction=intent.sort_direction or SortDirection.DESC,
        limit=intent.limit,
    )


def _resolve_total_spending(
    intent: QueryIntent,
) -> QueryIntent:
    return QueryIntent(
        entity=intent.entity,
        filters=intent.filters,
        metric="order_items.quantity * order_items.unit_price",
        aggregation=Aggregation.SUM,
        sort_direction=intent.sort_direction or SortDirection.DESC,
        limit=intent.limit,
    )