# ADR 001: Use a Controlled Workflow Instead of a Fully Autonomous Agent

## Status

Accepted

## Context

The Text-to-SQL system needs to perform a sequence of operations:

1. Analyze the user's request.
2. Identify ambiguity.
3. Retrieve relevant schema information.
4. Ask clarification questions when necessary.
5. Create a query plan.
6. Generate SQL.
7. Validate the generated SQL.
8. Execute the SQL safely.
9. Validate the result.
10. Generate a grounded answer.

The majority of these operations have predictable responsibilities and
well-defined boundaries.

Using a fully autonomous agent for the entire workflow would introduce
additional nondeterminism, complexity, latency, and debugging difficulty.

## Decision

Use a controlled application workflow that orchestrates deterministic
services and targeted LLM-powered components.

The LLM will be used where language understanding or generation provides
clear value.

Deterministic software will be preferred for:

- SQL parsing
- SQL safety validation
- database access
- query limits
- configuration
- authentication and authorization
- logging
- evaluation infrastructure

LLM-powered components will be used for:

- intent interpretation
- ambiguity analysis
- clarification generation
- query planning
- SQL generation
- constrained SQL repair
- natural-language answer generation

## Consequences

### Positive

- Easier to understand and debug.
- More deterministic execution flow.
- Easier to test individual components.
- Better control over database access.
- Easier to enforce security boundaries.
- Easier to measure individual pipeline stages.
- Lower risk of unnecessary agent behavior.

### Negative

- Some workflows may require explicit engineering.
- We may need to add new workflow logic as system capabilities grow.
- The system will not have unrestricted autonomous behavior.

## Alternatives Considered

### Fully autonomous agent

Rejected as the initial architecture because the workflow is sufficiently
well-defined that unrestricted autonomy would add complexity without enough
benefit.

### Simple LLM prompt → SQL

Rejected because it does not adequately address ambiguity, schema
intelligence, validation, security, execution safety, evaluation, or
observability.