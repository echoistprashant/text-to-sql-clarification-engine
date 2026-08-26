# Text-to-SQL Clarification Engineer

## Project Status

The repository contains a tested FastAPI Text-to-SQL pipeline. It analyzes read-only natural-language database questions, retrieves relevant schema context, extracts structured intent with Google Gemini, asks for clarification when the intent is ambiguous, builds and validates SQL, and can execute the result against the configured database.

The API, clarification workflow, schema retrieval components, SQL planner/compiler/validator, database executor, Gemini client, evaluation runner, and test suite are implemented. Analyses awaiting clarification are stored in an in-memory process-local dictionary.

## Features

- Natural-language database question analysis
- Structured intent extraction into an entity, filters, metric, aggregation, sort direction, and limit
- Google Gemini integration with a configurable model
- Database schema inspection through SQLAlchemy table, column, primary-key, and foreign-key metadata
- Schema retrieval using table relevance, foreign-key graph expansion, column value profiling, and value matching
- Ambiguity detection for ranking or aggregation requests without a metric
- Clarification question generation
- Clarification resolution for units purchased, order count, and total spending
- SQL generation from validated intent and schema information
- SQL safety and read-only validation at both the natural-language request and compiled SQL stages
- Parameterized SQL filters using named SQLAlchemy parameters
- Database answer formatting for empty, single-column, single-row, and multi-row results
- Request IDs through the `X-Request-ID` header, including generated IDs when one is not supplied
- Structured API errors with an `error.code` and `error.message` payload
- `/health` health endpoint
- `/ready` readiness endpoint that checks required configuration and the database connection
- Gemini retries for `google.genai.errors.ServerError`
- Exponential backoff between Gemini retries
- Configurable Gemini request timeout
- Environment-based application configuration loaded from environment variables and `.env`
- Automated evaluation of resolved and unresolved question cases
- Pytest test suite
- Ruff linting

## Architecture

The end-to-end flow is:

```text
Natural-language question
          |
          v
     Read-only request check
          |
          v
   Database schema inspection
          |
          v
    Schema retrieval and
    value matching
          |
          v
    Intent extraction
    (Google Gemini)
          |
          v
    Intent parsing and
    clarification detection
       /              \
      /                \
 Resolved          Unresolved
    |                    |
    v                    v
 SQL planning       Clarification
    |                    |
    v                    v
 SQL query          User answer
 validation              |
    |                    v
    v              Intent resolution
 SQL compilation          |
    |                    +
    v                    |
 Read-only SQL            |
 validation <------------+
    |
    v
 SQL execution
    |
    v
 Database result
    |
    v
 Formatted answer
```

The `/analyze` flow stops after producing SQL and parameters when the intent is resolved. The `/execute` flow runs the same analysis and executes resolved queries. When clarification is required, both flows return an `analysis_id`; the corresponding clarification endpoint updates the process-local stored analysis and either returns the next clarification or continues to SQL generation and, for `/execute/clarification`, execution.

## Project Structure

```text
text-to-sql-clarification-engine/
|
├── app/
│   ├── api/
│   │   └── main.py                  # FastAPI app, routes, models, errors
│   ├── config/
│   │   └── settings.py              # Environment-based settings
│   ├── db/
│   │   ├── connection.py            # SQLAlchemy engine and connection check
│   │   └── schema_inspector.py       # Database metadata inspection
│   ├── intent/
│   │   ├── ambiguity.py              # Ambiguity detection
│   │   ├── clarification.py           # Clarification request construction
│   │   ├── extractor.py               # LLM intent prompt
│   │   ├── models.py                  # Query intent models and enums
│   │   ├── parser.py                  # LLM JSON parsing
│   │   ├── resolver.py                # Clarification answer resolution
│   │   ├── safety.py                  # Read-only request validation
│   │   ├── state.py                   # Clarification state
│   │   └── workflow.py                # Clarification workflow
│   ├── llm/
│   │   ├── client.py                  # LLM client protocol
│   │   ├── context.py                 # Schema context formatting
│   │   ├── fake.py                    # Test LLM client
│   │   ├── gemini.py                  # Google Gemini client
│   │   └── schemas.py                 # Structured intent response schema
│   ├── pipeline/
│   │   ├── analysis.py                # Intent analysis pipeline
│   │   └── sql.py                     # SQL analysis and execution pipeline
│   ├── schema/
│   │   ├── graph.py                   # Foreign-key graph operations
│   │   ├── join_path.py               # Join path selection
│   │   ├── models.py                  # Schema and retrieval models
│   │   ├── profiler.py                # Column value profiling
│   │   ├── ranker.py                  # Table ranking
│   │   ├── retrieval.py                # Schema retrieval orchestration
│   │   ├── retriever.py               # Table retrieval
│   │   ├── serializer.py              # Schema serialization
│   │   └── value_matcher.py            # Question/value matching
│   └── sql/
│       ├── answer.py                  # Result-to-text formatting
│       ├── executor.py                # SQLAlchemy execution
│       ├── generator.py               # SQL compilation and parameters
│       ├── joins.py                   # Foreign-key join construction
│       ├── models.py                  # SQL query models
│       ├── planner.py                 # Intent-to-query planning
│       ├── safety.py                  # Compiled SQL read-only checks
│       └── validator.py               # Schema and query validation
├── evals/
│   ├── questions.py                   # Evaluation cases
│   └── runner.py                      # Evaluation execution and report
├── prompts/                           # Prompt resources
├── scripts/                           # Smoke scripts
├── tests/                             # Pytest tests
├── .env.example                       # Configuration template
├── .gitignore
├── pyproject.toml
├── README.md
└── uv.lock
```

## Requirements

- Python `>=3.12,<3.13`
- SQLAlchemy `>=2.0`
- `psycopg[binary] >=3.2` for PostgreSQL connectivity
- `python-dotenv >=1.0`
- FastAPI `>=0.141.1`

Development dependencies declared in `pyproject.toml` are `httpx`, `httpx2`, `pytest`, and `ruff`.

The Gemini client imports the Google GenAI SDK (`google.genai`). The current `pyproject.toml` does not declare that SDK as a project dependency, so it must be available in the environment when using the real Gemini client.

## Configuration

`app/config/settings.py` loads `.env` with `python-dotenv`. `DATABASE_URL` and `GEMINI_API_KEY` are required. The remaining settings have defaults shown below:

```dotenv
APP_NAME=Text-to-SQL Clarification Engine
APP_VERSION=0.1.0
APP_ENVIRONMENT=development
LOG_LEVEL=INFO

DATABASE_URL=your_database_url_here

GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
GEMINI_MAX_RETRIES=3
GEMINI_INITIAL_RETRY_DELAY_SECONDS=1.0
GEMINI_TIMEOUT_SECONDS=30.0
```

`GEMINI_MAX_RETRIES` and `GEMINI_INITIAL_RETRY_DELAY_SECONDS` control retry behavior. `GEMINI_TIMEOUT_SECONDS` is converted to milliseconds for the Google GenAI HTTP client. Retry counts and delay values must be non-negative; invalid numeric values raise a configuration error.

Do not commit real database credentials, API keys, or other secrets. The repository ignores `.env`; use `.env.example` as the template.

## API

The FastAPI application is defined in `app/api/main.py`.

### `GET /health`

Returns `{"status": "ok"}` without checking external dependencies.

### `GET /ready`

Returns `{"status": "ready"}` when `DATABASE_URL` and `GEMINI_API_KEY` are configured and `SELECT 1` succeeds on the database connection. Otherwise it returns a `503` error.

### `POST /analyze`

Accepts an `AnalyzeRequest` with:

```json
{
  "question": "Show customers from India"
}
```

Returns an `AnalyzeResponse` containing `analysis_id`, `question`, `resolved`, `intent`, optional `clarification`, optional `sql`, and optional `parameters`. An unresolved analysis is stored in memory and receives an `analysis_id`; a resolved analysis includes compiled SQL and parameters.

The `intent` contains `entity`, `filters`, `metric`, `aggregation`, `sort_direction`, and `limit`. Each filter contains `column`, `operator`, and `value`. The supported aggregation values are `count`, `sum`, `avg`, `min`, and `max`; sort directions are `asc` and `desc`.

### `POST /analyze/clarification`

Accepts a `ClarificationAnswerRequest`:

```json
{
  "analysis_id": "stored-analysis-id",
  "answer": "most units purchased"
}
```

Resolves the stored analysis and returns an `AnalyzeResponse`. The current metric clarification accepts answers for units purchased, orders, or total spending. Once resolved, the stored analysis is removed.

### `POST /execute`

Accepts the same `AnalyzeRequest` as `/analyze`. A resolved request is executed and returns an `ExecuteResponse` containing the analysis fields plus an `execution` object with `columns`, `rows`, and formatted `answer`. An unresolved request returns an `AnalyzeResponse` with a stored `analysis_id` instead of executing SQL.

### `POST /execute/clarification`

Accepts the same `ClarificationAnswerRequest` as `/analyze/clarification`. If the answer resolves the intent, the generated query is validated and executed, and the endpoint returns an `ExecuteResponse`. If it remains unresolved, it returns an `AnalyzeResponse` with the updated clarification state.

All routes use request observability middleware. Each response includes `X-Request-ID`, using the caller-provided value or a generated UUID. Validation and application errors use this shape:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "..."
  }
}
```

## SQL Safety

Natural-language questions are rejected when they contain a word-boundary match for `ALTER`, `CREATE`, `DELETE`, `DROP`, `GRANT`, `INSERT`, `MERGE`, `REVOKE`, `TRUNCATE`, or `UPDATE`.

For generated SQL, the safety validator:

- rejects empty SQL;
- permits exactly one statement;
- requires the statement to start with `SELECT`; and
- rejects the keywords `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `GRANT`, `REVOKE`, and `MERGE`.

Before compilation, query validation checks that referenced tables and columns exist, joins follow declared foreign-key relationships, aggregations and sort directions are supported, filter operators are supported, and limits are greater than zero. SQL filters are compiled as named parameters such as `:param_1`; execution passes the parameter dictionary separately through SQLAlchemy. The compiled SQL is checked again immediately before execution.

## Gemini Integration

`GeminiLLMClient` uses the configured `GEMINI_MODEL`, defaulting to `gemini-3.1-flash-lite`, and sends the intent prompt to `client.models.generate_content`. It requests `application/json` and the `INTENT_RESPONSE_SCHEMA`, whose fields are `entity`, `filters`, `metric`, `aggregation`, `sort_direction`, and `limit`.

The client retries `google.genai.errors.ServerError` up to `GEMINI_MAX_RETRIES` retries after the initial attempt. Delays use exponential backoff: `initial_delay * 2**attempt`. The configured timeout is passed to the GenAI HTTP client. Empty responses raise `RuntimeError("Gemini returned an empty response.")`; non-server errors are not retried and propagate to the application layer.

## Testing

Run the full pytest suite with:

```powershell
python -m pytest -v
```

Focused tests can be run by module, for example:

```powershell
python -m pytest tests/test_api.py -v
python -m pytest tests/test_gemini_client.py -v
python -m pytest tests/test_sql_safety.py tests/test_sql_validator.py -v
```

The test suite covers API behavior, clarification state and workflow, intent parsing and safety, schema inspection and retrieval, Gemini client behavior, SQL planning/generation/validation/safety/execution, and end-to-end pipeline behavior.

## Evaluation

Run the evaluation suite with:

```powershell
python -m evals.runner
```

The runner retrieves the configured database schema, creates a real `GeminiLLMClient`, analyzes each case with a maximum of three schema-retrieval hops, and compares the actual resolved state with each case's `expected_resolved` value. It reports the question, category, expected and actual resolution, generated SQL and parameters when present, and errors. The cases cover filters, simple retrieval, aggregation, clarification, no-result behavior, invalid input, and safety handling.

## Code Quality

Run Ruff with:

```powershell
ruff check .
```

## Development Workflow

1. Make changes.
2. Run focused tests.
3. Run the full pytest suite.
4. Run Ruff.
5. Run the evaluation suite.
6. Review `git diff` and `git status`.
7. Commit and push.

## Current Validation Status

Validated in the project `.venv` on 2026-08-26:

- `python -m pytest -v`: 184 passed.
- `ruff check .`: passed.
- `python -m evals.runner`: 15 passed, 0 failed.

The evaluation run also emitted the Google GenAI warning that direct automatic function calling through `Models.generate_content` is not recommended and that `Chat.send_message` should be used instead. The current client uses `Models.generate_content` for structured intent extraction.

## Known Limitations / Warnings

- Pending analyses are stored only in process memory, so they are not shared across processes and do not survive a restart.
- The current clarification workflow supports the `metric` field and three recognized metric choices: units purchased, orders, and total spending.
- The evaluation runner requires a configured database and Gemini API key because it uses the real schema inspector and Gemini client.
- The Google GenAI SDK import is used by the implementation but is not declared in the current `pyproject.toml` dependency list.
- The Google GenAI SDK emits an AFC warning for the direct `Models.generate_content` call; the implementation currently uses that call for intent extraction.

## License

TBD
