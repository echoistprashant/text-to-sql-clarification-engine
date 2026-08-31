from uuid import uuid4

from app.pipeline.sql import SQLAnalysisResult


class AnalysisStore:
    def __init__(self) -> None:
        self._analyses: dict[str, SQLAnalysisResult] = {}

    def create(
        self,
        result: SQLAnalysisResult,
    ) -> str:
        analysis_id = uuid4().hex

        self._analyses[analysis_id] = result

        return analysis_id

    def get(
        self,
        analysis_id: str,
    ) -> SQLAnalysisResult | None:
        return self._analyses.get(analysis_id)

    def update(
       self,
       analysis_id: str,
       result: SQLAnalysisResult,
    ) -> None:
       if analysis_id not in self._analyses:
        raise KeyError(
            f"Analysis '{analysis_id}' does not exist."
        )

       self._analyses[analysis_id] = result

    def delete(
        self,
        analysis_id: str,
    ) -> None:
        self._analyses.pop(
            analysis_id,
            None,
        )


        