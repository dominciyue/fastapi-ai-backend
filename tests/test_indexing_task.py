from types import SimpleNamespace

import pytest

from app.tasks.indexing import index_document


def test_index_document_runs_service_and_closes_session(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    db = SimpleNamespace(close=lambda: calls.append("closed"))

    class FakeIndexingService:
        def __init__(self, session) -> None:
            assert session is db

        async def run(self, task_id: str) -> None:
            calls.append(task_id)

    monkeypatch.setattr("app.tasks.indexing.SessionLocal", lambda: db)
    monkeypatch.setattr("app.tasks.indexing.IndexingService", FakeIndexingService)

    task_id = "task-123"
    result = index_document(task_id)

    assert result == task_id
    assert calls == ["task-123", "closed"]


def test_index_document_reraises_and_closes_session(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    db = SimpleNamespace(close=lambda: calls.append("closed"))

    class FakeIndexingService:
        def __init__(self, session) -> None:
            assert session is db

        async def run(self, task_id: str) -> None:  # noqa: ARG002
            raise RuntimeError("boom")

    monkeypatch.setattr("app.tasks.indexing.SessionLocal", lambda: db)
    monkeypatch.setattr("app.tasks.indexing.IndexingService", FakeIndexingService)

    with pytest.raises(RuntimeError, match="boom"):
        index_document("task-456")

    assert calls == ["closed"]
