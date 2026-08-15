from dataclasses import dataclass

from app.intent.models import QueryIntent


@dataclass(frozen=True)
class Ambiguity:
    field: str
    reason: str
    question: str


def detect_ambiguities(
    intent: QueryIntent,
) -> list[Ambiguity]:
    ambiguities: list[Ambiguity] = []

    if intent.sort_direction is not None and intent.metric is None:
        ambiguities.append(
            Ambiguity(
                field="metric",
                reason=(
                    "The query asks for a ranking, but does not "
                    "specify what should be measured."
                ),
                question=(
                    "What should 'most' or 'least' mean: "
                    "number of units, number of orders, "
                    "or total spending?"
                ),
            )
        )

    if intent.aggregation is not None and intent.metric is None:
        ambiguities.append(
            Ambiguity(
                field="metric",
                reason=(
                    "An aggregation was specified, but no metric "
                    "column was identified."
                ),
                question="Which field should be aggregated?",
            )
        )

    return ambiguities