from app.db.schema_inspector import get_schema
from app.pipeline.analysis import analyze_question, answer_analysis


class FakeLLMClient:
    def generate(self, prompt: str) -> str:
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


schema = get_schema()

result = analyze_question(
    "Which customers bought the most laptops?",
    schema,
    FakeLLMClient(),
    max_hops=3,
)

print("INITIAL STATE")
print("Resolved:", result.clarification.resolved)
print("Clarification:", result.clarification.clarification)
print("Schema tables:", result.schema.tables)
print("Value matches:", result.schema.value_matches)

resolved = answer_analysis(
    result,
    "Most units purchased",
)

print("\nRESOLVED STATE")
print("Resolved:", resolved.clarification.resolved)
print("Intent:", resolved.clarification.intent)
print("Schema tables:", resolved.schema.tables)
print("Join path:", resolved.schema.join_path)