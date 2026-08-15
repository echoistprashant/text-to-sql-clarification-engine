from dataclasses import dataclass

from app.intent.ambiguity import Ambiguity


@dataclass(frozen=True)
class ClarificationOption:
    value: str
    label: str


@dataclass(frozen=True)
class ClarificationRequest:
    field: str
    question: str
    options: list[ClarificationOption]


def build_clarification(
    ambiguity: Ambiguity,
) -> ClarificationRequest:
    if ambiguity.field == "metric":
        return ClarificationRequest(
            field="metric",
            question='What should "most" mean?',
            options=[
                ClarificationOption(
                    value="units_purchased",
                    label="Most units purchased",
                ),
                ClarificationOption(
                    value="orders",
                    label="Most orders",
                ),
                ClarificationOption(
                    value="total_spending",
                    label="Highest total spending",
                ),
            ],
        )

    return ClarificationRequest(
        field=ambiguity.field,
        question=ambiguity.question,
        options=[],
    )