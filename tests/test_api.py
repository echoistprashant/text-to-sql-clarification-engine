from fastapi.testclient import TestClient

from app.api.main import (
    app,
    get_database_schema,
    get_llm_client,
)
from app.db.schema_inspector import get_schema
from app.llm.fake import FakeLLMClient


class FakeTestLLMClient(FakeLLMClient):
    def __init__(self):
        super().__init__(
            response="""
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
            """,
        )

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
        json={"question": ""},
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
            "question": "Show customers from India",
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