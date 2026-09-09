from dataclasses import dataclass

from app.intent.extractor import extract_intent
from app.intent.safety import validate_read_only_request
from app.intent.state import ClarificationState
from app.intent.workflow import (
    answer_clarification,
    create_clarification_state,
)
from app.llm.client import LLMClient
from app.llm.context import build_llm_schema_context
from app.schema.models import (
    DatabaseSchema,
    SchemaRetrievalResult,
)
from app.schema.retrieval import retrieve_schema


@dataclass(frozen=True)
class AnalysisResult:
    question: str
    schema: SchemaRetrievalResult
    clarification: ClarificationState


from app.intent.models import QueryIntent
from app.schema.graph import build_schema_graph
from app.schema.join_path import select_join_path


def _collect_intent_tables(intent: QueryIntent) -> set[str]:
    tables = set()
    if intent.entity:
        tables.add(intent.entity)
    if intent.metric and "." in intent.metric:
        tables.add(intent.metric.split(".", 1)[0])
    if intent.group_by and "." in intent.group_by:
        tables.add(intent.group_by.split(".", 1)[0])
    for f in intent.filters:
        if "." in f.column:
            tables.add(f.column.split(".", 1)[0])
    return tables


def refine_schema_with_intent(
    schema: DatabaseSchema,
    schema_result: SchemaRetrievalResult,
    intent: QueryIntent,
) -> SchemaRetrievalResult:
    intent_tables = _collect_intent_tables(intent)
    for m in schema_result.value_matches:
        intent_tables.add(m.table_name)

    if not intent_tables:
        return schema_result

    current_tables = list(schema_result.tables)
    for t in sorted(intent_tables):
        if t not in current_tables:
            current_tables.append(t)

    graph = build_schema_graph(schema)
    join_path = select_join_path(graph, intent_tables)

    return SchemaRetrievalResult(
        tables=current_tables,
        value_matches=schema_result.value_matches,
        ranked_tables=schema_result.ranked_tables,
        join_path=join_path or schema_result.join_path,
    )


def analyze_question(
    question: str,
    schema: DatabaseSchema,
    llm_client: LLMClient,
    max_hops: int = 2,
) -> AnalysisResult:
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    validate_read_only_request(
        question,
    )

    schema_result = retrieve_schema(
        schema,
        question,
        max_hops=max_hops,
    )

    schema_context = build_llm_schema_context(
        schema,
        schema_result,
    )

    intent = extract_intent(
        question,
        schema_context,
        llm_client,
    )

    refined_schema = refine_schema_with_intent(
        schema,
        schema_result,
        intent,
    )

    clarification = create_clarification_state(
        question,
        intent,
    )

    return AnalysisResult(
        question=question,
        schema=refined_schema,
        clarification=clarification,
    )


def answer_analysis(
    result: AnalysisResult,
    answer: str,
    schema: DatabaseSchema | None = None,
) -> AnalysisResult:
    clarification = answer_clarification(
        result.clarification,
        answer,
    )

    schema_result = result.schema
    if schema is not None and clarification.intent is not None:
        schema_result = refine_schema_with_intent(
            schema,
            schema_result,
            clarification.intent,
        )

    return AnalysisResult(
        question=result.question,
        schema=schema_result,
        clarification=clarification,
    )
