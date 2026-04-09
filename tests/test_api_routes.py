from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.metrics import metrics_store
from app.main import app
from app.models import Document, DocumentStatus, IndexingTask, TaskStatus
from app.schemas.chat import ChatMeta, ChatResponse, ChatSource, TokenUsage
from app.schemas.retrieval import RetrievalHit, RetrievalMeta, RetrievalResponse


class FakeSession:
    def __init__(self) -> None:
        self.documents: dict[UUID, Document] = {}
        self.tasks: dict[UUID, IndexingTask] = {}

    def add(self, obj: object) -> None:
        now = datetime.now(UTC)

        if isinstance(obj, Document):
            obj.id = obj.id or uuid4()
            obj.created_at = obj.created_at or now
            obj.updated_at = obj.updated_at or now
            obj.chunk_count = obj.chunk_count or 0
            self.documents[obj.id] = obj
            return

        if isinstance(obj, IndexingTask):
            obj.id = obj.id or uuid4()
            obj.created_at = obj.created_at or now
            obj.updated_at = obj.updated_at or now
            self.tasks[obj.id] = obj

    def commit(self) -> None:
        return None

    def refresh(self, obj: object) -> None:
        if isinstance(obj, IndexingTask):
            obj.updated_at = obj.updated_at or datetime.now(UTC)

    def get(self, model: type[object], key: object) -> object | None:
        if model is Document:
            return self.documents.get(key)
        if model is IndexingTask:
            return self.tasks.get(key)
        return None


def _override_db(fake_db: FakeSession):
    def override():
        yield fake_db

    return override


def test_healthcheck(monkeypatch) -> None:
    monkeypatch.setattr("app.main.init_db", lambda: None)
    monkeypatch.setattr("app.main.setup_logging", lambda: None)
    metrics_store.reset()

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_check_healthy(monkeypatch) -> None:
    monkeypatch.setattr("app.main.init_db", lambda: None)
    monkeypatch.setattr("app.main.setup_logging", lambda: None)
    monkeypatch.setattr("app.main.check_database_connection", lambda: True)
    monkeypatch.setattr("app.main.check_redis_connection", lambda: True)
    metrics_store.reset()

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"database": True, "redis": True},
    }


def test_readiness_check_degraded(monkeypatch) -> None:
    monkeypatch.setattr("app.main.init_db", lambda: None)
    monkeypatch.setattr("app.main.setup_logging", lambda: None)
    monkeypatch.setattr("app.main.check_database_connection", lambda: True)
    monkeypatch.setattr("app.main.check_redis_connection", lambda: False)
    metrics_store.reset()

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "degraded",
        "checks": {"database": True, "redis": False},
    }


def test_upload_document(monkeypatch, tmp_path: Path) -> None:
    fake_db = FakeSession()
    stored_path = tmp_path / "uploaded.md"
    stored_path.write_text("# uploaded", encoding="utf-8")
    metrics_store.reset()

    monkeypatch.setattr("app.main.init_db", lambda: None)
    monkeypatch.setattr("app.main.setup_logging", lambda: None)
    monkeypatch.setattr("app.api.routes.documents.save_upload_file", lambda _: stored_path)
    app.dependency_overrides[get_db] = _override_db(fake_db)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("sample.md", b"# sample", "text/markdown")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Document uploaded successfully."
    assert payload["document"]["filename"] == "sample.md"
    assert payload["document"]["status"] == DocumentStatus.uploaded
    assert len(fake_db.documents) == 1


def test_queue_indexing_and_get_task(monkeypatch) -> None:
    fake_db = FakeSession()
    metrics_store.reset()
    document = Document(
        id=uuid4(),
        filename="sample.md",
        content_type="text/markdown",
        storage_path="storage/uploads/sample.md",
        status=DocumentStatus.uploaded,
        chunk_count=0,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        metadata_={"suffix": ".md"},
    )
    fake_db.documents[document.id] = document

    monkeypatch.setattr("app.main.init_db", lambda: None)
    monkeypatch.setattr("app.main.setup_logging", lambda: None)
    monkeypatch.setattr(
        "app.api.routes.documents.celery_app.send_task",
        lambda *_args, **_kwargs: SimpleNamespace(id="celery-task-123"),
    )
    app.dependency_overrides[get_db] = _override_db(fake_db)

    try:
        with TestClient(app) as client:
            create_response = client.post(
                "/api/v1/documents/index",
                json={"document_id": str(document.id), "metadata": {}},
            )
            assert create_response.status_code == 200

            payload = create_response.json()
            task_id = payload["id"]
            get_response = client.get(f"/api/v1/tasks/{task_id}")
    finally:
        app.dependency_overrides.clear()

    assert get_response.status_code == 200
    assert payload["document_id"] == str(document.id)
    assert payload["status"] == TaskStatus.queued
    assert document.status == DocumentStatus.indexing
    task = next(iter(fake_db.tasks.values()))
    assert task.celery_task_id == "celery-task-123"
    assert get_response.json()["id"] == task_id


def test_retrieval_search(monkeypatch) -> None:
    metrics_store.reset()
    hits = [RetrievalHit(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename="guide.md",
        content="retrieved context",
        score=0.12,
        metadata={"source": "guide.md"},
    )]

    async def fake_search(
        self,
        query: str,
        top_k: int,
        request_id: str = "unknown",
        rerank: bool | None = None,
    ):  # noqa: ARG001
        assert query == "how to deploy"
        assert top_k == 3
        assert request_id == "route-req-1"
        assert rerank is True
        return RetrievalResponse(
            query=query,
            hits=hits,
            meta=RetrievalMeta(
                request_id=request_id,
                latency_ms=4,
                cache_hit=False,
                reranked=True,
                candidate_count=5,
            ),
        )

    monkeypatch.setattr("app.main.init_db", lambda: None)
    monkeypatch.setattr("app.main.setup_logging", lambda: None)
    monkeypatch.setattr("app.services.retrieval.RetrievalService.search", fake_search)
    app.dependency_overrides[get_db] = _override_db(FakeSession())

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/retrieval/search",
                headers={"X-Request-ID": "route-req-1"},
                json={"query": "how to deploy", "top_k": 3, "rerank": True},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "how to deploy"
    assert len(payload["hits"]) == 1
    assert payload["hits"][0]["filename"] == "guide.md"
    assert payload["meta"]["request_id"] == "route-req-1"
    assert payload["meta"]["cache_hit"] is False
    assert payload["meta"]["reranked"] is True
    assert payload["meta"]["candidate_count"] == 5
    assert response.headers["X-Request-ID"] == "route-req-1"


def test_chat_query(monkeypatch) -> None:
    metrics_store.reset()
    chat_response = ChatResponse(
        answer="This service supports upload and retrieval.",
        sources=[ChatSource(filename="guide.md", content="retrieved context", score=0.12)],
        meta=ChatMeta(
            request_id="chat-req-1",
            latency_ms=9,
            retrieval_cache_hit=True,
            retrieval_reranked=True,
            retrieval_candidate_count=6,
            token_usage=TokenUsage(
                prompt_tokens_estimate=10,
                completion_tokens_estimate=6,
                total_tokens_estimate=16,
            ),
        ),
    )

    async def fake_answer(
        self,
        query: str,
        top_k: int,
        system_prompt: str | None,
        request_id: str = "unknown",
        rerank: bool | None = None,
    ):  # noqa: ARG001
        assert query == "what does it do"
        assert top_k == 2
        assert system_prompt == "answer briefly"
        assert request_id == "chat-req-1"
        assert rerank is True
        return chat_response

    monkeypatch.setattr("app.main.init_db", lambda: None)
    monkeypatch.setattr("app.main.setup_logging", lambda: None)
    monkeypatch.setattr("app.services.chat.ChatService.answer", fake_answer)
    app.dependency_overrides[get_db] = _override_db(FakeSession())

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/chat/query",
                headers={"X-Request-ID": "chat-req-1"},
                json={
                    "query": "what does it do",
                    "top_k": 2,
                    "system_prompt": "answer briefly",
                    "rerank": True,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "This service supports upload and retrieval."
    assert payload["sources"][0]["filename"] == "guide.md"
    assert payload["meta"]["request_id"] == "chat-req-1"
    assert payload["meta"]["retrieval_cache_hit"] is True
    assert payload["meta"]["retrieval_reranked"] is True
    assert payload["meta"]["retrieval_candidate_count"] == 6
    assert payload["meta"]["token_usage"]["total_tokens_estimate"] == 16
    assert response.headers["X-Request-ID"] == "chat-req-1"


def test_chat_stream(monkeypatch) -> None:
    metrics_store.reset()
    sources = [ChatSource(filename="guide.md", content="retrieved context", score=0.12)]

    async def fake_generator() -> AsyncGenerator[str, None]:
        yield "token-1 "
        yield "token-2"

    async def fake_stream_answer(
        self,
        query: str,
        top_k: int,
        system_prompt: str | None,
        request_id: str = "unknown",
        rerank: bool | None = None,
    ):  # noqa: ARG001
        assert query == "stream it"
        assert top_k == 1
        assert system_prompt is None
        assert request_id == "stream-req-1"
        assert rerank is False
        return sources, fake_generator()

    monkeypatch.setattr("app.main.init_db", lambda: None)
    monkeypatch.setattr("app.main.setup_logging", lambda: None)
    monkeypatch.setattr("app.services.chat.ChatService.stream_answer", fake_stream_answer)
    app.dependency_overrides[get_db] = _override_db(FakeSession())

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/chat/stream",
                headers={"X-Request-ID": "stream-req-1"},
                json={"query": "stream it", "top_k": 1, "rerank": False},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert 'event: sources' in response.text
    assert 'event: token' in response.text
    assert 'event: done' in response.text
    assert 'guide.md' in response.text
    assert 'token-1 ' in response.text
    assert 'token-2' in response.text
    assert response.headers["X-Request-ID"] == "stream-req-1"
    assert "X-Response-Time-Ms" in response.headers


def test_metrics_endpoint(monkeypatch) -> None:
    monkeypatch.setattr("app.main.init_db", lambda: None)
    monkeypatch.setattr("app.main.setup_logging", lambda: None)
    monkeypatch.setattr("app.main.check_database_connection", lambda: True)
    monkeypatch.setattr("app.main.check_redis_connection", lambda: True)
    metrics_store.reset()

    with TestClient(app) as client:
        client.get("/health")
        client.get("/health/ready")
        response = client.get("/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["http"]["total_requests"] >= 2
    assert payload["http"]["requests_by_path"]["/health"] >= 1
    assert payload["http"]["requests_by_path"]["/health/ready"] >= 1
    assert "average_latency_ms" in payload["http"]
    assert "retrieval" in payload
