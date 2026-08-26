import logging
import time
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.db.connection import check_database_connection
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

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Text-to-SQL Clarification Engine",
    version="0.1.0",
    description=(
        "Production-oriented Text-to-SQL API that analyzes "
        "natural-language database questions, detects ambiguity, "
        "resolves clarifications, generates safe read-only SQL, "
        "and executes validated queries."
    ),
    openapi_tags=[
        {
            "name": "system",
            "description": (
                "Application health and readiness endpoints."
            ),
        },
        {
            "name": "analysis",
            "description": (
                "Natural-language question analysis and "
                "clarification endpoints."
            ),
        },
        {
            "name": "execution",
            "description": (
                "SQL execution and clarification endpoints."
            ),
        },
    ],
)


_analysis_store: dict[str, SQLAnalysisResult] = {}


class AnalyzeRequest(BaseModel):
    question: str = Field(
        min_length=1,
        description="Natural-language database question.",
        examples=[
            "How many customers are from India?",
        ],
    )


class ClarificationAnswerRequest(BaseModel):
    analysis_id: str = Field(
        min_length=1,
        description="ID of the unresolved analysis.",
    )
    answer: str = Field(
        min_length=1,
        description="Answer to the clarification question.",
        examples=[
            "Use total order value.",
        ],
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


class APIErrorResponse(BaseModel):
    error: dict[str, str]


def _error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str | None = None,
) -> JSONResponse:
    response = JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
            }
        },
    )

    if request_id is not None:
        response.headers["X-Request-ID"] = request_id

    return response


def _classify_value_error(
    message: str,
) -> tuple[int, str]:
    if (
        "read-only database questions" in message
        or "Forbidden SQL operation" in message
        or "Only SELECT statements" in message
    ):
        return 400, "UNSUPPORTED_OPERATION"

    if (
        "Cannot execute SQL" in message
        or "Cannot build SQL" in message
        or "SQL query" in message
        or "Expected a qualified column name" in message
        or "Unsupported filter operator" in message
    ):
        return 400, "INVALID_QUERY"

    return 400, "INVALID_REQUEST"


@app.middleware("http")
async def request_observability(
    request: Request,
    call_next,
):
    request_id = request.headers.get(
        "X-Request-ID",
    )

    if not request_id:
        request_id = uuid4().hex

    request.state.request_id = request_id

    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        logger.exception(
            "Request failed: method=%s path=%s "
            "request_id=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            request_id,
            duration_ms,
        )

        raise

    duration_ms = (
        time.perf_counter() - start_time
    ) * 1000

    response.headers["X-Request-ID"] = request_id

    logger.info(
        "Request completed: method=%s path=%s "
        "status=%s request_id=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        request_id,
        duration_ms,
    )

    return response


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    logger.warning(
        "Request validation failed: method=%s "
        "path=%s request_id=%s",
        request.method,
        request.url.path,
        request_id,
    )

    return _error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="Request validation failed.",
        request_id=request_id,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    logger.warning(
        "HTTP error: method=%s path=%s "
        "status=%s request_id=%s",
        request.method,
        request.url.path,
        exc.status_code,
        request_id,
    )

    if exc.status_code == 404:
        code = "NOT_FOUND"
    elif exc.status_code == 400:
        code = "BAD_REQUEST"
    else:
        code = "HTTP_ERROR"

    message = (
        str(exc.detail)
        if isinstance(exc.detail, str)
        else "HTTP request failed."
    )

    return _error_response(
        status_code=exc.status_code,
        code=code,
        message=message,
        request_id=request_id,
    )


@app.exception_handler(ValueError)
async def value_error_handler(
    request: Request,
    exc: ValueError,
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    message = str(exc)

    status_code, code = _classify_value_error(
        message,
    )

    logger.warning(
        "Application error: method=%s path=%s "
        "code=%s request_id=%s",
        request.method,
        request.url.path,
        code,
        request_id,
    )

    return _error_response(
        status_code=status_code,
        code=code,
        message=message,
        request_id=request_id,
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    logger.exception(
        "Unhandled exception: method=%s path=%s "
        "request_id=%s",
        request.method,
        request.url.path,
        request_id,
        exc_info=exc,
    )

    return _error_response(
        status_code=500,
        code="INTERNAL_ERROR",
        message="An unexpected internal error occurred.",
        request_id=request_id,
    )


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


def _get_analysis(
    analysis_id: str,
) -> SQLAnalysisResult:
    result = _analysis_store.get(
        analysis_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found.",
        )

    return result


@app.get(
    "/health",
    tags=["system"],
    summary="Health check",
    description=(
        "Returns a lightweight liveness response without "
        "checking external dependencies."
    ),
)
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/ready",
    tags=["system"],
    summary="Readiness check",
    description=(
        "Checks whether required configuration is available "
        "and the database connection is reachable."
    ),
    responses={
        503: {
            "model": APIErrorResponse,
            "description": (
                "Required configuration or database "
                "connection is unavailable."
            ),
        },
    },
)
def readiness_check() -> dict[str, str]:
    settings = get_settings()

    if not settings.database_url:
        raise HTTPException(
            status_code=503,
            detail="Database configuration is unavailable.",
        )

    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=503,
            detail="Gemini configuration is unavailable.",
        )

    try:
        check_database_connection()
    except SQLAlchemyError:
        logger.warning(
            "Database readiness check failed.",
        )
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        ) from None

    return {"status": "ready"}


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    tags=["analysis"],
    summary="Analyze a database question",
    description=(
        "Analyzes a natural-language database question, "
        "detects ambiguity, generates a clarification when "
        "necessary, and produces read-only SQL when the "
        "intent is sufficiently resolved."
    ),
    responses={
        400: {
            "model": APIErrorResponse,
            "description": "Invalid or unsupported database query.",
        },
        422: {
            "model": APIErrorResponse,
            "description": "Request validation failed.",
        },
        500: {
            "model": APIErrorResponse,
            "description": "Unexpected internal server error.",
        },
    },
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
    tags=["analysis"],
    summary="Resolve an analysis clarification",
    description=(
        "Applies a user's clarification answer to a previously "
        "unresolved analysis. The analysis remains stored if "
        "additional clarification is required."
    ),
    responses={
        400: {
            "model": APIErrorResponse,
            "description": "Invalid clarification answer.",
        },
        404: {
            "model": APIErrorResponse,
            "description": "Analysis ID was not found.",
        },
        422: {
            "model": APIErrorResponse,
            "description": "Request validation failed.",
        },
        500: {
            "model": APIErrorResponse,
            "description": "Unexpected internal server error.",
        },
    },
)
def analyze_clarification(
    request: ClarificationAnswerRequest,
    schema: DatabaseSchema = Depends(
        get_database_schema,
    ),
) -> AnalyzeResponse:
    result = _get_analysis(
        request.analysis_id,
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
    tags=["execution"],
    summary="Analyze and execute a database question",
    description=(
        "Analyzes a natural-language database question and "
        "executes the generated read-only SQL when the intent "
        "is resolved. Returns a clarification response when "
        "additional information is required."
    ),
    responses={
        400: {
            "model": APIErrorResponse,
            "description": "Invalid or unsupported database query.",
        },
        422: {
            "model": APIErrorResponse,
            "description": "Request validation failed.",
        },
        500: {
            "model": APIErrorResponse,
            "description": "Unexpected internal server error.",
        },
    },
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
    tags=["execution"],
    summary="Resolve clarification and execute SQL",
    description=(
        "Applies a clarification answer to a previously "
        "unresolved analysis and executes the resulting "
        "read-only SQL when the intent becomes resolved."
    ),
    responses={
        400: {
            "model": APIErrorResponse,
            "description": "Invalid clarification or query.",
        },
        404: {
            "model": APIErrorResponse,
            "description": "Analysis ID was not found.",
        },
        422: {
            "model": APIErrorResponse,
            "description": "Request validation failed.",
        },
        500: {
            "model": APIErrorResponse,
            "description": "Unexpected internal server error.",
        },
    },
)
def execute_clarification(
    request: ClarificationAnswerRequest,
    schema: DatabaseSchema = Depends(
        get_database_schema,
    ),
) -> ExecuteResponse | AnalyzeResponse:
    result = _get_analysis(
        request.analysis_id,
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