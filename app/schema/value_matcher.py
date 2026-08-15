import re

from app.schema.models import ColumnValueProfile, ValueMatch


def normalize_token(token: str) -> str:
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]

    return token


def normalize_text(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    tokens = [
        normalize_token(token)
        for token in value.split()
    ]

    return " ".join(tokens)


def find_value_matches(
    profile: ColumnValueProfile,
    question: str,
) -> list[ValueMatch]:
    normalized_question = normalize_text(question)
    question_terms = set(normalized_question.split())

    matches = []

    for value in profile.values:
        normalized_value = normalize_text(value)
        value_terms = set(normalized_value.split())

        if question_terms & value_terms:
            matches.append(
                ValueMatch(
                    table_name=profile.table_name,
                    column_name=profile.column_name,
                    value=value,
                )
            )

    return matches