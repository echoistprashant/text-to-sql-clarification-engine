from dataclasses import dataclass

from app.llm.client import LLMClient
from app.pipeline.analysis import (
    AnalysisResult,
    analyze_question,
    answer_analysis,
)
from app.schema.models import DatabaseSchema
from app.sql.generator import compile_sql
from app.sql.models import SQLQuery
from app.sql.planner import plan_sql_query
from app.sql.safety import validate_read_only_sql
from app.sql.validator import validate_sql_query


@dataclass(frozen=True)
class SQLAnalysisResult:
    analysis: AnalysisResult
    query: SQLQuery | None = None
    sql: str | None = None
    parameters: dict[str, str] | None = None


def analyze_for_sql(
    question: str,
    schema: DatabaseSchema,
    llm_client: LLMClient,
    max_hops: int = 2,
) -> SQLAnalysisResult:
    analysis = analyze_question(
        question,
        schema,
        llm_client,
        max_hops=max_hops,
    )

    if not analysis.clarification.resolved:
        return SQLAnalysisResult(
            analysis=analysis,
        )

    return _build_sql_result(
        analysis,
        schema,
    )


def answer_sql_clarification(
    result: SQLAnalysisResult,
    answer: str,
    schema: DatabaseSchema,
) -> SQLAnalysisResult:
    if result.analysis.clarification.resolved:
        raise ValueError(
            "The SQL analysis is already resolved."
        )

    updated_analysis = answer_analysis(
        result.analysis,
        answer,
    )

    if not updated_analysis.clarification.resolved:
        return SQLAnalysisResult(
            analysis=updated_analysis,
        )

    return _build_sql_result(
        updated_analysis,
        schema,
    )


def _build_sql_result(
    analysis: AnalysisResult,
    schema: DatabaseSchema,
) -> SQLAnalysisResult:
    if not analysis.clarification.resolved:
        raise ValueError(
            "Cannot build SQL from unresolved clarification."
        )

    intent = analysis.clarification.intent

    query = plan_sql_query(
        schema,
        intent,
        analysis.schema,
    )

    validate_sql_query(
        schema,
        query,
    )

    compiled = compile_sql(
        query,
    )

    validate_read_only_sql(
        compiled.sql,
    )

    return SQLAnalysisResult(
        analysis=analysis,
        query=query,
        sql=compiled.sql,
        parameters=compiled.parameters,
    )