from dataclasses import dataclass

from app.db.schema_inspector import get_schema
from app.pipeline.sql import analyze_for_sql
from evals.questions import (
    EVALUATION_CASES,
    EvaluationCase,
)


@dataclass(frozen=True)
class EvaluationResult:
    case: EvaluationCase
    resolved: bool
    passed: bool
    sql: str | None
    parameters: dict[str, str] | None
    error: str | None = None


def run_case(
    case: EvaluationCase,
    schema,
    llm_client,
) -> EvaluationResult:
    try:
        result = analyze_for_sql(
            case.question,
            schema,
            llm_client,
            max_hops=3,
        )

        resolved = result.analysis.clarification.resolved

        passed = resolved == case.expected_resolved

        return EvaluationResult(
            case=case,
            resolved=resolved,
            passed=passed,
            sql=result.sql,
            parameters=result.parameters,
        )

    except ValueError as exc:
        if case.expected_resolved is False:
            return EvaluationResult(
                case=case,
                resolved=False,
                passed=True,
                sql=None,
                parameters=None,
                error=f"{type(exc).__name__}: {exc}",
            )

        return EvaluationResult(
            case=case,
            resolved=False,
            passed=False,
            sql=None,
            parameters=None,
            error=f"{type(exc).__name__}: {exc}",
        )


def run_evaluation() -> list[EvaluationResult]:
    from app.api.main import get_llm_client

    schema = get_schema()
    llm_client = get_llm_client()

    results = []

    for case in EVALUATION_CASES:
        result = run_case(
            case,
            schema,
            llm_client,
        )

        results.append(result)

    return results


def print_report(
    results: list[EvaluationResult],
) -> None:
    total = len(results)
    passed = sum(result.passed for result in results)
    failed = total - passed

    print("PHASE 6 EVALUATION")
    print("==================")
    print(f"TOTAL:  {total}")
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")

    print()

    for result in results:
        status = "PASS" if result.passed else "FAIL"

        print(f"[{status}] {result.case.name}")

        print(f"  Question: {result.case.question!r}")

        print(f"  Category: {result.case.category}")

        print(f"  Expected resolved: {result.case.expected_resolved}")

        print(f"  Actual resolved: {result.resolved}")

        if result.sql is not None:
            print("  SQL:")
            print(result.sql)

        if result.parameters is not None:
            print(f"  Parameters: {result.parameters}")

        if result.error is not None:
            print(f"  Error: {result.error}")

        print()


if __name__ == "__main__":
    results = run_evaluation()
    print_report(results)
