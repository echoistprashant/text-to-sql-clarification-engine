from app.intent.ambiguity import Ambiguity
from app.intent.clarification import build_clarification


def test_metric_ambiguity_builds_clarification_options():
    ambiguity = Ambiguity(
        field="metric",
        reason="The ranking metric is missing.",
        question="What should be measured?",
    )

    request = build_clarification(ambiguity)

    assert request.field == "metric"
    assert request.question == 'What should "most" mean?'

    assert [option.value for option in request.options] == [
        "units_purchased",
        "orders",
        "total_spending",
    ]


def test_unknown_ambiguity_uses_existing_question():
    ambiguity = Ambiguity(
        field="some_field",
        reason="Unknown ambiguity",
        question="Please clarify this field.",
    )

    request = build_clarification(ambiguity)

    assert request.field == "some_field"
    assert request.question == "Please clarify this field."
    assert request.options == []