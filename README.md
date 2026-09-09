# Text-to-SQL Clarification Engine

Production-ready, portfolio-quality Text-to-SQL engine with an interactive Clarification Engineer built with Python 3.12, FastAPI, PostgreSQL 16, SQLAlchemy 2.0, and Google Gemini.

## Overview

The **Text-to-SQL Clarification Engine** translates natural-language database inquiries into verified, performant, read-only SQL queries. Unlike naive text-to-sql systems that hallucinate or generate erroneous SQL when queries are ambiguous, this engine detects underspecified requests (such as "Show top 5 products" or "Which customers are best?"), initiates an interactive clarification loop with the user, resolves the ambiguity into structured query intent, and then compiles and executes safe parameterized SQL.

## Key Features

- **Flexible LLM Providers (OpenRouter & Gemini)**: Uses OpenRouter API (`google/gemini-2.5-flash`, `openai/gpt-4o-mini`, etc.) or the official Google GenAI Gemini SDK with strict JSON structured outputs (`entity`, `filters`, `metric`, `aggregation`, `group_by`, `sort_direction`, `limit`).
- **Interactive Clarification Loop**: Automatically detects missing metrics or ambiguous entities and asks targeted clarifying questions. Stores conversation states in an in-memory analysis store (`AnalysisStore`) with unique `analysis_id` handles.
- **Intelligent Schema Retrieval & Join Path Resolution**: Inspects database metadata via SQLAlchemy, profiles column values, normalizes terms (handling singular/plural and business synonyms like *revenue*, *sales*, *units*), and uses Dijkstra's shortest path algorithm over schema foreign-key graphs to construct multi-table join paths.
- **Safe Read-Only SQL Compiler**: Validates allowed tables, columns, joins, and aggregations against the real database schema. Rejects non-read-only queries (e.g. `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `GRANT`, `COPY`, `EXEC`, `CALL`).
- **Parameterized Queries**: Compiles SQL filters into named SQLAlchemy bind parameters (e.g. `:param_1`), completely preventing SQL injection.
- **Production API & Observability**: FastAPI REST API with structured errors, request IDs via `X-Request-ID` headers, request logging, and connection pooling.
- **Containerized Deployment**: Multi-stage Dockerfile and Docker Compose orchestration with health/readiness checks (`/health` and `/ready`).
- **Reproducible Seed Data**: Complete PostgreSQL schema definition (`database/schema.sql`) and deterministic seed script (`database/seed.sql`) containing 5 customers, 4 orders, 6 order items, 6 products, and 4 payments with a verified $148,000.00 total revenue.

---

## Architecture

```text
Natural-Language Question
         |
         v
    [Safety Check] (Rejects destructive keywords: DROP, DELETE, etc.)
         |
         v
[Schema Inspector & Profiler] (Fetches tables, columns, foreign keys, values)
         |
         v
 [Schema Retriever & Ranker] (Graph traversal, concept synonyms & ranking)
         |
         v
 [Gemini Intent Extractor] (Structured JSON: entity, metric, group_by, etc.)
         |
         v
[Ambiguity Detector]
       /           \
 (Ambiguous)    (Resolved)
     /               \
    v                 v
[Generate Clarification]   [Join Path Selector] (Multi-hop foreign key path)
    |                         |
    v                         v
[Store Analysis State]     [SQL Planner & Validator] (Validates against schema)
    |                         |
    v                         v
(Wait for User Response)   [SQL Generator] (Parameterized SELECT statement)
    |                         |
    v                         v
[Resolve Clarification]    [Safety Guard] (Enforces read-only SELECT)
    |                         |
    +------------------------>+
                              |
                              v
                     [PostgreSQL Executor] (Executes parameterized query)
                              |
                              v
                     [Formatted Response] (JSON rows, columns & text summary)
```

---

## Project Structure

```text
text-to-sql-clarification-engine/
├── app/
│   ├── api/
│   │   ├── analysis_store.py      # In-memory TTL/state store for pending clarifications
│   │   └── main.py                # FastAPI endpoints, middleware, response models
│   ├── config/
│   │   └── settings.py            # Environment configuration with pydantic/dotenv
│   ├── db/
│   │   ├── connection.py          # SQLAlchemy engine, connection pooling, and health checks
│   │   └── schema_inspector.py    # Database metadata reflection (tables, cols, PKs, FKs)
│   ├── intent/
│   │   ├── ambiguity.py           # Ambiguity detection algorithms
│   │   ├── clarification.py       # Clarification question generation
│   │   ├── extractor.py           # LLM intent prompt with file/in-memory fallback
│   │   ├── models.py              # QueryIntent, IntentFilter, Aggregation, SortDirection
│   │   ├── parser.py              # Robust JSON parser for LLM outputs
│   │   ├── resolver.py            # Clarification answer resolver (revenue, units, orders)
│   │   ├── safety.py              # Natural language prompt injection and safety guard
│   │   ├── state.py               # Clarification state management
│   │   └── workflow.py            # Clarification workflow transitions
│   ├── llm/
│   │   ├── client.py              # LLM client interface protocol
│   │   ├── context.py             # Schema context serializer for prompts
│   │   ├── fake.py                # Deterministic fake LLM client for unit tests
│   │   ├── gemini.py              # Official google-genai client with retry/backoff
│   │   └── schemas.py             # GenAI structured output JSON schemas
│   ├── pipeline/
│   │   ├── analysis.py            # End-to-end analysis pipeline
│   │   └── sql.py                 # SQL analysis, compilation, and execution pipeline
│   ├── schema/
│   │   ├── graph.py               # Schema graph construction and breadth-first search
│   │   ├── join_path.py           # Shortest-path join resolution across multiple tables
│   │   ├── models.py              # DatabaseSchema, TableSchema, ColumnSchema
│   │   ├── profiler.py            # Distinct value profiler for text columns
│   │   ├── ranker.py              # Table scoring and relevance ranker
│   │   ├── retrieval.py           # Schema retrieval orchestrator
│   │   ├── retriever.py           # Concept-to-table mapper and seed finder
│   │   ├── serializer.py          # Schema-to-prompt serialization
│   │   └── value_matcher.py       # Exact and fuzzy value matching in questions
│   └── sql/
│       ├── answer.py              # Natural-language answer formatter
│       ├── executor.py            # SQLAlchemy parameterized query executor
│       ├── generator.py           # AST to parameterized SQL compiler
│       ├── joins.py               # Join clause generator
│       ├── models.py              # SQLQuery, SQLColumn, SQLJoin AST representations
│       ├── planner.py             # Intent-to-SQL AST planner
│       ├── safety.py              # Read-only SQL validator & forbidden keyword scanner
│       └── validator.py           # Schema integrity checker for planned SQL
├── database/
│   ├── schema.sql                 # DDL definitions for PostgreSQL
│   └── seed.sql                   # Deterministic seed data ($148,000 revenue)
├── prompts/
│   └── intent.txt                 # Canonical prompt template for Gemini intent extraction
├── scripts/
│   ├── smoke_gemini.py            # Smoke test for Gemini client
│   └── smoke_phase2.py            # Smoke test for end-to-end pipeline
├── tests/
│   ├── test_api.py                # FastAPI endpoints and error handling tests
│   ├── test_regression_queries.py # 10 production regression queries
│   ├── ...                        # 211 comprehensive unit & integration tests
├── Dockerfile                     # Multi-stage container definition
├── docker-compose.yml             # Service orchestration (PostgreSQL + FastAPI)
├── pyproject.toml                 # uv / pip dependency declarations
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Docker and Docker Compose
- A Google Gemini API Key

### Local Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/echoistprashant/text-to-sql-clarification-engine.git
   cd text-to-sql-clarification-engine
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Configure Environment**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   ```dotenv
   DATABASE_URL=postgresql+psycopg://app_user:dev_password_123@localhost:5432/text_to_sql
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```

4. **Start PostgreSQL**:
   ```bash
   docker compose up -d postgres
   ```
   *(Optional)* If starting with an empty database:
   ```bash
   docker exec -i text-to-sql-postgres psql -U app_user -d text_to_sql < database/schema.sql
   docker exec -i text-to-sql-postgres psql -U app_user -d text_to_sql < database/seed.sql
   ```

5. **Run the FastAPI server**:
   ```bash
   uv run uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

---

## API Endpoints

- `GET /health` - Lightweight liveness check (`{"status": "ok"}`)
- `GET /ready` - Readiness check verifying database connectivity and configuration (`{"status": "ready"}`)
- `POST /analyze` - Analyzes a question, extracts intent, generates SQL or clarification (does not execute SQL)
- `POST /analyze/clarification` - Submits an answer to a clarification question from `/analyze`
- `POST /execute` - Analyzes a question and immediately executes the generated SQL if resolved
- `POST /execute/clarification` - Submits an answer to a clarification question and executes the resulting query

---

## Verification & Testing

### Running Tests
Execute the entire test suite with `uv`:
```bash
uv run pytest -v
```
**Results**: 211 passed in ~12 seconds.

### Code Quality & Linting
Run Ruff check and formatting:
```bash
uv run ruff check .
uv run ruff format --check .
```
**Results**: All checks passed! 96 files formatted.

---

## License

MIT License.
