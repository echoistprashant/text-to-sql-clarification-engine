import pytest

from app.intent.safety import validate_read_only_request


@pytest.mark.parametrize(
    "question",
    [
        "Delete all customers",
        "DELETE FROM customers",
        "Update customer names",
        "Insert a new customer",
        "Drop the customers table",
        "Alter the customers table",
        "Create a new table",
        "Truncate customers",
        "Grant access to customers",
        "Revoke access from customers",
        "Merge customers with another table",
    ],
)
def test_mutating_requests_are_rejected(question):
    with pytest.raises(
        ValueError,
        match="Only read-only database questions are supported",
    ):
        validate_read_only_request(question)


@pytest.mark.parametrize(
    "question",
    [
        "Show all customers",
        "Show customers from India",
        "How many customers are there?",
        "Which products cost more than 50000?",
        "Which customers bought the most laptops?",
        "How many laptops were sold?",
    ],
)
def test_read_only_requests_are_allowed(question):
    validate_read_only_request(question)


def test_empty_question_is_not_rejected_by_safety_guard():
    validate_read_only_request("")


def test_whitespace_only_question_is_not_rejected_by_safety_guard():
    validate_read_only_request("   ")


def test_mutating_keyword_is_detected_case_insensitively():
    with pytest.raises(
        ValueError,
        match="Only read-only database questions are supported",
    ):
        validate_read_only_request(
            "please DELETE all customers"
        )


def test_mutating_keyword_is_detected_with_extra_whitespace():
    with pytest.raises(
        ValueError,
        match="Only read-only database questions are supported",
    ):
        validate_read_only_request(
            "Delete    all    customers"
        )