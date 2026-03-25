from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models import Document, IndexingTask, TaskStatus
from app.models.document import DocumentStatus
from app.services.indexing import IndexingService


@pytest.mark.asyncio
async def test_run_marks_task_failed_after_rollback(monkeypatch: pytest.MonkeyPatch) -> None:
    task_id = str(uuid4())
    document_id = uuid4()
    task = SimpleNamespace(
        id=uuid4(),
        document_id=document_id,
        status=TaskStatus.queued,
        detail=None,
    )
    document = SimpleNamespace(
        id=document_id,
        filename="sample.md",
        storage_path="storage/uploads/sample.md",
        status=DocumentStatus.uploaded,
        error_message=None,
        chunk_count=0,
    )

    class FakeDB:
        def __init__(self) -> None:
            self.commit_calls = 0
            self.rollback_calls = 0

        def get(self, model, key):
            if model is IndexingTask:
                return task
            if model is Document:
                return document
            return None

        def execute(self, _stmt) -> None:
            return None

        def add(self, _obj) -> None:
            return None

        def commit(self) -> None:
            self.commit_calls += 1
            if self.commit_calls == 3:
                raise RuntimeError("expected 1536 dimensions, not 1024")

        def refresh(self, _obj) -> None:
            return None

        def rollback(self) -> None:
            self.rollback_calls += 1

    async def fake_embed(self, texts: list[str]) -> list[list[float]]:  # noqa: ARG001
        return [[0.1, 0.2, 0.3]]

    monkeypatch.setattr("app.services.indexing.parse_document", lambda _path: "hello world")
    monkeypatch.setattr("app.services.indexing.chunk_text", lambda _text: ["chunk-1"])
    monkeypatch.setattr("app.services.llm_client.OpenAICompatibleClient.embed", fake_embed)

    db = FakeDB()
    service = IndexingService(db)

    result = await service.run(task_id)

    assert db.rollback_calls == 1
    assert document.status == DocumentStatus.failed
    assert "expected 1536 dimensions, not 1024" in document.error_message
    assert result is task
    assert task.status == TaskStatus.failed
    assert "expected 1536 dimensions, not 1024" in task.detail
