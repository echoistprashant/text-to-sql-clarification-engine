from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.db.schema_inspector import get_schema
from app.intent.models import Aggregation, SortDirection
from app.llm.client import LLMClient
from app.llm.gemini import GeminiLLMClient
from app.pipeline.sql import (
    SQLAnalysisResult,
    SQLAnswerResult,
    analyze_for_sql,
    answer_sql_clarification,
    execute_sql_analysis,
)
from app.schema.models import DatabaseSchema

app = FastAPI(
    title="Text-to-SQL Clarification Engine",
    version="0.1.0",
)


_analysis_store: dict[str, SQLAnalysisResult] = {}


class AnalyzeRequest(BaseModel):
    question: str = Field(
        min_length=1,
        description="Natural-language database question.",
    )


class ClarificationAnswerRequest(BaseModel):
    analysis_id: str = Field(
        min_length=1,
        description="ID of the unresolved analysis.",
    )
    answer: str = Field(
        min_length=1,
        description="Answer to the clarification question.",
    )


class IntentFilterResponse(BaseModel):
    column: str
    operator: str
    value: str


class IntentResponse(BaseModel):
    entity: str | None
    filters: list[IntentFilterResponse]
    metric: str | None
    aggregation: Aggregation | None
    sort_direction: SortDirection | None
    limit: int | None


class ClarificationResponse(BaseModel):
    field: str
    question: str


class ExecutionResponse(BaseModel):
    columns: list[str]
    rows: list[list[object]]
    answer: str


class AnalyzeResponse(BaseModel):
    analysis_id: str | None = None
    question: str
    resolved: bool
    intent: IntentResponse
    clarification: ClarificationResponse | None = None
    sql: str | None = None
    parameters: dict[str, str] | None = None


class ExecuteResponse(BaseModel):
    analysis_id: str | None = None
    question: str
    resolved: bool
    intent: IntentResponse
    clarification: ClarificationResponse | None = None
    sql: str | None = None
    parameters: dict[str, str] | None = None
    execution: ExecutionResponse | None = None


def get_database_schema() -> DatabaseSchema:
    return get_schema()


def get_llm_client() -> LLMClient:
    return GeminiLLMClient()


def _build_intent_response(
    result: SQLAnalysisResult,
) -> IntentResponse:
    intent = result.analysis.clarification.intent

    return IntentResponse(
        entity=intent.entity,
        filters=[
            IntentFilterResponse(
                column=item.column,
                operator=item.operator,
                value=item.value,
            )
            for item in intent.filters
        ],
        metric=intent.metric,
        aggregation=intent.aggregation,
        sort_direction=intent.sort_direction,
        limit=intent.limit,
    )


def _build_clarification_response(
    result: SQLAnalysisResult,
) -> ClarificationResponse | None:
    clarification = (
        result.analysis.clarification.clarification
    )

    if clarification is None:
        return None

    return ClarificationResponse(
        field=clarification.field,
        question=clarification.question,
    )


def _build_analysis_response(
    result: SQLAnalysisResult,
    analysis_id: str | None = None,
) -> AnalyzeResponse:
    return AnalyzeResponse(
        analysis_id=analysis_id,
        question=result.analysis.question,
        resolved=result.analysis.clarification.resolved,
        intent=_build_intent_response(result),
        clarification=_build_clarification_response(
            result,
        ),
        sql=result.sql,
        parameters=result.parameters,
    )


def _build_execution_response(
    result: SQLAnswerResult,
    analysis_id: str | None = None,
) -> ExecuteResponse:
    sql_result = SQLAnalysisResult(
        analysis=result.analysis,
        query=result.query,
        sql=result.sql,
        parameters=result.parameters,
    )

    return ExecuteResponse(
        analysis_id=analysis_id,
        question=result.analysis.question,
        resolved=True,
        intent=_build_intent_response(
            sql_result,
        ),
        clarification=None,
        sql=result.sql,
        parameters=result.parameters,
        execution=ExecutionResponse(
            columns=result.execution.columns,
            rows=[
                list(row)
                for row in result.execution.rows
            ],
            answer=result.answer,
        ),
    )


def _store_analysis(
    result: SQLAnalysisResult,
) -> str:
    analysis_id = uuid4().hex

    _analysis_store[analysis_id] = result

    return analysis_id


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
)
def analyze(
    request: AnalyzeRequest,
    schema: DatabaseSchema = Depends(
        get_database_schema,
    ),
    llm_client: LLMClient = Depends(
        get_llm_client,
    ),
) -> AnalyzeResponse:
    result = analyze_for_sql(
        request.question,
        schema,
        llm_client,
        max_hops=3,
    )

    if result.analysis.clarification.resolved:
        return _build_analysis_response(result)

    analysis_id = _store_analysis(result)

    return _build_analysis_response(
        result,
        analysis_id=analysis_id,
    )


@app.post(
    "/analyze/clarification",
    response_model=AnalyzeResponse,
)
def analyze_clarification(
    request: ClarificationAnswerRequest,
    schema: DatabaseSchema = Depends(
        get_database_schema,
    ),
) -> AnalyzeResponse:
    result = _analysis_store.get(
        request.analysis_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found.",
        )

    updated_result = answer_sql_clarification(
        result,
        request.answer,
        schema,
    )

    if updated_result.analysis.clarification.resolved:
        _analysis_store.pop(
            request.analysis_id,
            None,
        )

        return _build_analysis_response(
            updated_result,
        )

    _analysis_store[
        request.analysis_id
    ] = updated_result

    return _build_analysis_response(
        updated_result,
        analysis_id=request.analysis_id,
    )


@app.post(
    "/execute",
    response_model=ExecuteResponse | AnalyzeResponse,
)
def execute(
    request: AnalyzeRequest,
    schema: DatabaseSchema = Depends(
        get_database_schema,
    ),
    llm_client: LLMClient = Depends(
        get_llm_client,
    ),
) -> ExecuteResponse | AnalyzeResponse:
    result = analyze_for_sql(
        request.question,
        schema,
        llm_client,
        max_hops=3,
    )

    if not result.analysis.clarification.resolved:
        analysis_id = _store_analysis(result)

        return _build_analysis_response(
            result,
            analysis_id=analysis_id,
        )

    execution_result = execute_sql_analysis(
        result,
    )

    return _build_execution_response(
        execution_result,
    )


@app.post(
    "/execute/clarification",
    response_model=ExecuteResponse | AnalyzeResponse,
)
def execute_clarification(
    request: ClarificationAnswerRequest,
    schema: DatabaseSchema = Depends(
        get_database_schema,
    ),
) -> ExecuteResponse | AnalyzeResponse:
    result = _analysis_store.get(
        request.analysis_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found.",
        )

    updated_result = answer_sql_clarification(
        result,
        request.answer,
        schema,
    )

    if not updated_result.analysis.clarification.resolved:
        _analysis_store[
            request.analysis_id
        ] = updated_result

        return _build_analysis_response(
            updated_result,
            analysis_id=request.analysis_id,
        )

    _analysis_store.pop(
        request.analysis_id,
        None,
    )

    execution_result = execute_sql_analysis(
        updated_result,
    )

    return _build_execution_response(
        execution_result,
    )