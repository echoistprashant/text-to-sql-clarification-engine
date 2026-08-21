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


def analyze_question(
    question: str,
    schema: DatabaseSchema,
    llm_client: LLMClient,
    max_hops: int = 2,
) -> AnalysisResult:
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

    clarification = create_clarification_state(
        question,
        intent,
    )

    return AnalysisResult(
        question=question,
        schema=schema_result,
        clarification=clarification,
    )


def answer_analysis(
    result: AnalysisResult,
    answer: str,
) -> AnalysisResult:
    clarification = answer_clarification(
        result.clarification,
        answer,
    )

    return AnalysisResult(
        question=result.question,
        schema=result.schema,
        clarification=clarification,
    )