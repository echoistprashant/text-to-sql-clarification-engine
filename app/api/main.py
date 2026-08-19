from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from app.db.schema_inspector import get_schema
from app.intent.models import Aggregation, SortDirection
from app.llm.client import LLMClient
from app.llm.gemini import GeminiLLMClient
from app.pipeline.analysis import analyze_question
from app.schema.models import DatabaseSchema

app = FastAPI(
    title="Text-to-SQL Clarification Engine",
    version="0.1.0",
)


class AnalyzeRequest(BaseModel):
    question: str = Field(
        min_length=1,
        description="Natural-language database question.",
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


class AnalyzeResponse(BaseModel):
    question: str
    resolved: bool
    intent: IntentResponse
    clarification: ClarificationResponse | None = None


def get_database_schema() -> DatabaseSchema:
    return get_schema()


def get_llm_client() -> LLMClient:
    return GeminiLLMClient()


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
    result = analyze_question(
        request.question,
        schema,
        llm_client,
        max_hops=3,
    )

    clarification = result.clarification.clarification
    intent = result.clarification.intent

    intent_response = IntentResponse(
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

    clarification_response = None

    if clarification is not None:
        clarification_response = ClarificationResponse(
            field=clarification.field,
            question=clarification.question,
        )

    return AnalyzeResponse(
        question=result.question,
        resolved=result.clarification.resolved,
        intent=intent_response,
        clarification=clarification_response,
    )