from unittest.mock import Mock

import pytest

from app.api.analysis_store import AnalysisStore
from app.pipeline.sql import SQLAnalysisResult


def _result() -> SQLAnalysisResult:
    return Mock(spec=SQLAnalysisResult)


def test_analysis_store_creates_and_gets_analysis():
    store = AnalysisStore()
    result = _result()

    analysis_id = store.create(result)

    assert analysis_id
    assert store.get(analysis_id) is result


def test_analysis_store_returns_none_for_unknown_analysis():
    store = AnalysisStore()

    assert store.get("missing") is None


def test_analysis_store_updates_analysis():
    store = AnalysisStore()
    first = _result()
    second = _result()

    analysis_id = store.create(first)

    store.update(
        analysis_id,
        second,
    )

    assert store.get(analysis_id) is second


def test_analysis_store_deletes_analysis():
    store = AnalysisStore()
    result = _result()

    analysis_id = store.create(result)

    store.delete(analysis_id)

    assert store.get(analysis_id) is None


def test_analysis_store_delete_missing_analysis_is_safe():
    store = AnalysisStore()

    store.delete("missing")

def test_analysis_store_update_missing_analysis_raises():
    store = AnalysisStore()
    result = _result()

    with pytest.raises(
        KeyError,
        match="Analysis 'missing' does not exist.",
    ):
        store.update(
            "missing",
            result,
        )