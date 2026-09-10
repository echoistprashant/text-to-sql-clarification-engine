import re

from app.schema.graph import build_schema_graph, expand_tables
from app.schema.models import DatabaseSchema, TableSchema

_CONCEPT_TABLE_MAPPINGS: dict[str, set[str]] = {
    # revenue / sales / spending / amounts
    "revenue": {"orders", "order_items", "payments"},
    "sales": {"orders", "order_items"},
    "sale": {"orders", "order_items"},
    "spend": {"orders", "order_items"},
    "spending": {"orders", "order_items"},
    "spent": {"orders", "order_items"},
    "amount": {"orders", "payments"},
    "paid": {"payments", "orders"},
    "pay": {"payments"},
    "payment": {"payments"},
    "payments": {"payments"},
    # units / quantity / items
    "unit": {"order_items"},
    "units": {"order_items"},
    "quantity": {"order_items"},
    "purchased": {"order_items", "orders"},
    "purchase": {"orders", "order_items"},
    "item": {"order_items", "products"},
    "items": {"order_items", "products"},
    # customer / buyer / user
    "customer": {"customers"},
    "customers": {"customers"},
    "user": {"customers"},
    "users": {"customers"},
    "buyer": {"customers"},
    "buyers": {"customers"},
    # product / category
    "product": {"products", "order_items"},
    "products": {"products", "order_items"},
    "category": {"products"},
    "categories": {"products"},
    # order
    "order": {"orders", "order_items"},
    "orders": {"orders", "order_items"},
}


def _extract_words(text: str) -> set[str]:
    return set(re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower()))


def _normalize_name(name: str) -> set[str]:
    terms = {name.lower()}
    if name.lower().endswith("s") and len(name) > 3:
        terms.add(name.lower()[:-1])
    parts = name.lower().split("_")
    for part in parts:
        terms.add(part)
        if part.endswith("s") and len(part) > 3:
            terms.add(part[:-1])
    return terms


def find_seed_tables(
    schema: DatabaseSchema,
    question: str,
) -> set[str]:
    question_terms = _extract_words(question)
    seed_tables: set[str] = set()

    for table in schema.tables:
        table_terms = _normalize_name(table.name)
        for column in table.columns:
            table_terms.update(_normalize_name(column.name))

        if question_terms & table_terms:
            seed_tables.add(table.name)

        for term in question_terms:
            if (
                term in _CONCEPT_TABLE_MAPPINGS
                and table.name in _CONCEPT_TABLE_MAPPINGS[term]
            ):
                seed_tables.add(table.name)

    return seed_tables


def score_table_relevance(
    table: TableSchema,
    question: str,
) -> int:
    question_terms = _extract_words(question)
    score = 0

    table_terms = _normalize_name(table.name)
    if question_terms & table_terms:
        score += 3

    for column in table.columns:
        if question_terms & _normalize_name(column.name):
            score += 1

    for term in question_terms:
        if (
            term in _CONCEPT_TABLE_MAPPINGS
            and table.name in _CONCEPT_TABLE_MAPPINGS[term]
        ):
            score += 2

    return score


def retrieve_tables(
    schema: DatabaseSchema,
    question: str,
    max_hops: int = 1,
) -> list[TableSchema]:
    seed_tables = find_seed_tables(schema, question)

    if not seed_tables:
        return list(schema.tables)

    graph = build_schema_graph(schema)

    candidate_tables = expand_tables(
        graph,
        seed_tables,
        max_hops=max_hops,
    )

    scored_tables = [
        (
            table,
            score_table_relevance(table, question),
        )
        for table in schema.tables
        if table.name in candidate_tables
    ]

    scored_tables.sort(key=lambda item: (-item[1], item[0].name))

    return [table for table, _ in scored_tables]
