from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.api.main import (
    app,
    get_database_schema,
    get_llm_client,
)
from app.config.settings import Settings
from app.db.schema_inspector import get_schema
from app.llm.fake import FakeLLMClient


class FakeTestLLMClient(FakeLLMClient):
    def __init__(self):
        super().__init__(response="")

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)

        if "Show customers from India" in prompt:
            return """
            {
                "entity": "customers",
                "filters": [
                    {
                        "column": "customers.country",
                        "operator": "=",
                        "value": "India"
                    }
                ],
                "metric": null,
                "aggregation": null,
                "sort_direction": null,
                "limit": null
            }
            """

        return """
        {
            "entity": "customers",
            "filters": [],
            "metric": null,
            "aggregation": null,
            "sort_direction": "desc",
            "limit": null
        }
        """


def override_schema():
    return get_schema()


def override_llm_client():
    return FakeTestLLMClient()


client = TestClient(app)


def setup_function():
    app.dependency_overrides[
        get_database_schema
    ] = override_schema

    app.dependency_overrides[
        get_llm_client
    ] = override_llm_client


def teardown_function():
    app.dependency_overrides.clear()


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
    }


def test_analyze_rejects_empty_question():
    response = client.post(
        "/analyze",
        json={
            "question": "",
        },
    )

    assert response.status_code == 422


def test_analyze_rejects_missing_question():
    response = client.post(
        "/analyze",
        json={},
    )

    assert response.status_code == 422


def test_analyze_uses_injected_dependencies():
    response = client.post(
        "/analyze",
        json={
            "question": (
                "Show customers from India"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["question"] == (
        "Show customers from India"
    )

    assert body["resolved"] is True
    assert body["clarification"] is None


def test_analyze_returns_structured_intent():
    response = client.post(
        "/analyze",
        json={
            "question": (
                "Show customers from India"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["question"] == (
        "Show customers from India"
    )

    assert body["resolved"] is True

    assert body["intent"]["entity"] == "customers"
    assert body["intent"]["metric"] is None
    assert body["intent"]["aggregation"] is None
    assert body["intent"]["sort_direction"] is None
    assert body["intent"]["limit"] is None

    assert body["intent"]["filters"] == [
        {
            "column": "customers.country",
            "operator": "=",
            "value": "India",
        }
    ]

    assert body["clarification"] is None


def test_analyze_returns_clarification():
    response = client.post(
        "/analyze",
        json={
            "question": (
                "Which customers bought "
                "the most laptops?"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["question"] == (
        "Which customers bought "
        "the most laptops?"
    )

    assert body["resolved"] is False
    assert body["analysis_id"] is not None

    assert body["clarification"] is not None
    assert body["clarification"]["field"] == "metric"

    assert body["sql"] is None
    assert body["parameters"] is None


def test_analyze_clarification_resolves_metric():
    first_response = client.post(
        "/analyze",
        json={
            "question": (
                "Which customers bought "
                "the most laptops?"
            ),
        },
    )

    assert first_response.status_code == 200

    first_body = first_response.json()

    assert first_body["resolved"] is False
    assert first_body["analysis_id"] is not None

    analysis_id = first_body["analysis_id"]

    response = client.post(
        "/analyze/clarification",
        json={
            "analysis_id": analysis_id,
            "answer": "most units purchased",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["question"] == (
        "Which customers bought "
        "the most laptops?"
    )

    assert body["resolved"] is True

    assert body["intent"]["entity"] == "customers"

    assert body["intent"]["metric"] == (
        "order_items.quantity"
    )

    assert body["intent"]["aggregation"] == "sum"

    assert body["intent"]["sort_direction"] == "desc"

    assert body["clarification"] is None

    assert body["analysis_id"] is None


def test_analyze_returns_null_sql_when_unresolved():
    response = client.post(
        "/analyze",
        json={
            "question": (
                "Which customers bought "
                "the most laptops?"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["resolved"] is False
    assert body["analysis_id"] is not None
    assert body["sql"] is None
    assert body["parameters"] is None


def test_analyze_clarification_returns_sql():
    first_response = client.post(
        "/analyze",
        json={
            "question": (
                "Which customers bought "
                "the most laptops?"
            ),
        },
    )

    assert first_response.status_code == 200

    analysis_id = first_response.json()["analysis_id"]

    assert analysis_id is not None

    response = client.post(
        "/analyze/clarification",
        json={
            "analysis_id": analysis_id,
            "answer": "most units purchased",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["resolved"] is True

    assert body["sql"] is not None

    assert "SELECT customers.name" in body["sql"]
    assert "SUM(order_items.quantity)" in body["sql"]
    assert "INNER JOIN orders" in body["sql"]
    assert "INNER JOIN order_items" in body["sql"]
    assert "INNER JOIN products" in body["sql"]
    assert "ORDER BY metric_value DESC" in body["sql"]

    assert body["parameters"] == {
        "param_1": "Laptop Pro 15",
    }

    assert body["analysis_id"] is None


def test_analyze_clarification_rejects_unknown_analysis():
    response = client.post(
        "/analyze/clarification",
        json={
            "analysis_id": "does-not-exist",
            "answer": "most units purchased",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
    "error": {
        "code": "NOT_FOUND",
        "message": "Analysis not found.",
    }
}


def test_execute_returns_clarification_when_unresolved():
    response = client.post(
        "/execute",
        json={
            "question": (
                "Which customers bought "
                "the most laptops?"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["resolved"] is False
    assert body["analysis_id"] is not None

    assert body["clarification"] is not None
    assert body["clarification"]["field"] == "metric"

    assert body["sql"] is None
    assert body["parameters"] is None


def test_execute_returns_database_answer():
    response = client.post(
        "/execute",
        json={
            "question": (
                "Show customers from India"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["resolved"] is True
    assert body["analysis_id"] is None

    assert body["sql"] is not None

    assert body["parameters"] == {
        "param_1": "India",
    }

    assert body["execution"] is not None

    assert body["execution"]["columns"] == [
        "name",
    ]

    assert body["execution"]["rows"]

    names = {
        row[0]
        for row in body["execution"]["rows"]
    }

    assert "Amit Sharma" in names
    assert "Priya Singh" in names
    assert "Raman Sharma" in names

    assert body["execution"]["answer"]

    assert body["execution"]["answer"].startswith(
        "name: "
    )


def test_execute_clarification_returns_database_answer():
    first_response = client.post(
        "/execute",
        json={
            "question": (
                "Which customers bought "
                "the most laptops?"
            ),
        },
    )

    assert first_response.status_code == 200

    first_body = first_response.json()

    assert first_body["resolved"] is False
    assert first_body["analysis_id"] is not None

    analysis_id = first_body["analysis_id"]

    response = client.post(
        "/execute/clarification",
        json={
            "analysis_id": analysis_id,
            "answer": "most units purchased",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["resolved"] is True
    assert body["analysis_id"] is None

    assert body["intent"]["entity"] == "customers"

    assert body["intent"]["metric"] == (
        "order_items.quantity"
    )

    assert body["intent"]["aggregation"] == "sum"

    assert body["intent"]["sort_direction"] == "desc"

    assert body["clarification"] is None

    assert body["sql"] is not None

    assert "SELECT customers.name" in body["sql"]
    assert "SUM(order_items.quantity)" in body["sql"]
    assert "INNER JOIN orders" in body["sql"]
    assert "INNER JOIN order_items" in body["sql"]
    assert "INNER JOIN products" in body["sql"]
    assert "WHERE products.name = :param_1" in body["sql"]
    assert "GROUP BY customers.name" in body["sql"]
    assert "ORDER BY metric_value DESC" in body["sql"]

    assert body["parameters"] == {
        "param_1": "Laptop Pro 15",
    }

    assert body["execution"] is not None

    assert body["execution"]["columns"] == [
        "name",
        "metric_value",
    ]

    assert body["execution"]["rows"]

    assert body["execution"]["rows"] == [
        ["Rahul Sharma", 1],
    ]

    assert body["execution"]["answer"] == (
        "name: Rahul Sharma, metric_value: 1"
    )


def test_execute_clarification_rejects_unknown_analysis():
    response = client.post(
        "/execute/clarification",
        json={
            "analysis_id": "does-not-exist",
            "answer": "most units purchased",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
    "error": {
        "code": "NOT_FOUND",
        "message": "Analysis not found.",
    }
}


def test_analyze_validation_error_uses_api_error_format():
    response = client.post(
        "/analyze",
        json={
            "question": "",
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed.",
        }
    }


def test_analyze_missing_question_uses_api_error_format():
    response = client.post(
        "/analyze",
        json={},
    )

    assert response.status_code == 422

    assert response.json() == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed.",
        }
    }


def test_unknown_analysis_uses_api_error_format():
    response = client.post(
        "/analyze/clarification",
        json={
            "analysis_id": "does-not-exist",
            "answer": "most units purchased",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Analysis not found.",
        }
    }


def test_unknown_execute_analysis_uses_api_error_format():
    response = client.post(
        "/execute/clarification",
        json={
            "analysis_id": "does-not-exist",
            "answer": "most units purchased",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Analysis not found.",
        }
    }


def test_destructive_request_uses_unsupported_operation_error():
    response = client.post(
        "/analyze",
        json={
            "question": "Delete all customers",
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["error"]["code"] == (
        "UNSUPPORTED_OPERATION"
    )

    assert body["error"]["message"] == (
        "Only read-only database questions are supported."
    )    


def test_unresolved_analysis_is_stored():
    response = client.post(
        "/analyze",
        json={
            "question": "Which customers bought the most laptops?"
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["resolved"] is False
    assert body["analysis_id"] is not None
    assert body["clarification"] is not None


def test_resolved_analysis_does_not_create_analysis_id():
    response = client.post(
        "/analyze",
        json={
            "question": "Show customers from India"
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["resolved"] is True
    assert body["analysis_id"] is None


def test_analyze_clarification_removes_resolved_analysis():
    response = client.post(
        "/analyze",
        json={
            "question": "Which customers bought the most laptops?"
        },
    )

    assert response.status_code == 200

    analysis_id = response.json()["analysis_id"]

    assert analysis_id is not None

    clarification_response = client.post(
        "/analyze/clarification",
        json={
            "analysis_id": analysis_id,
            "answer": "Most units purchased",
        },
    )

    assert clarification_response.status_code == 200

    body = clarification_response.json()

    assert body["resolved"] is True
    assert body["analysis_id"] is None

    second_response = client.post(
        "/analyze/clarification",
        json={
            "analysis_id": analysis_id,
            "answer": "Most orders",
        },
    )

    assert second_response.status_code == 404

    assert second_response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Analysis not found.",
        }
    }


def test_execute_clarification_removes_resolved_analysis():
    response = client.post(
        "/execute",
        json={
            "question": "Which customers bought the most laptops?"
        },
    )

    assert response.status_code == 200

    analysis_id = response.json()["analysis_id"]

    assert analysis_id is not None

    clarification_response = client.post(
        "/execute/clarification",
        json={
            "analysis_id": analysis_id,
            "answer": "Most units purchased",
        },
    )

    assert clarification_response.status_code == 200

    body = clarification_response.json()

    assert body["resolved"] is True
    assert body["execution"] is not None

    second_response = client.post(
        "/execute/clarification",
        json={
            "analysis_id": analysis_id,
            "answer": "Most orders",
        },
    )

    assert second_response.status_code == 404

    assert second_response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Analysis not found.",
        }
    }    

def test_health_check_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }
    assert response.headers["X-Request-ID"]


def test_request_id_is_generated():
    response = client.get("/health")

    request_id = response.headers.get(
        "X-Request-ID"
    )

    assert request_id
    assert len(request_id) == 32


def test_request_id_is_preserved():
    request_id = "test-request-123"

    response = client.get(
        "/health",
        headers={
            "X-Request-ID": request_id,
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_validation_error_contains_request_id():
    request_id = "validation-request-123"

    response = client.post(
        "/analyze",
        json={},
        headers={
            "X-Request-ID": request_id,
        },
    )

    assert response.status_code == 422
    assert response.headers["X-Request-ID"] == request_id
    assert response.json() == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed.",
        }
    }


def test_unknown_analysis_contains_request_id():
    request_id = "missing-analysis-123"

    response = client.post(
        "/analyze/clarification",
        json={
            "analysis_id": "does-not-exist",
            "answer": "most units purchased",
        },
        headers={
            "X-Request-ID": request_id,
        },
    )

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == request_id
    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Analysis not found.",
        }
    }    

def test_readiness_check_returns_ready():
    settings = Settings(
        app_name="Test App",
        app_version="0.1.0",
        environment="test",
        log_level="INFO",
        database_url="sqlite:///test.db",
        gemini_api_key="test-key",
        gemini_model="test-model",
        gemini_max_retries=3,
        gemini_initial_retry_delay_seconds=1.0,
    )

    with (
        patch(
            "app.api.main.get_settings",
            return_value=settings,
        ),
        patch(
            "app.api.main.check_database_connection"
        ) as check_database,
    ):
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
    }
    assert response.headers["X-Request-ID"]
    check_database.assert_called_once()


def test_readiness_check_fails_when_database_is_unavailable():
    error = OperationalError(
        "Database unavailable.",
        {},
        RuntimeError("connection failed"),
    )

    with patch(
        "app.api.main.check_database_connection",
        side_effect=error,
    ):
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "HTTP_ERROR",
            "message": "Database is unavailable.",
        }
    }
    assert response.headers["X-Request-ID"]