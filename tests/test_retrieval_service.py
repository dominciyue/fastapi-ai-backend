from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.schemas.retrieval import RetrievalHit
from app.services.retrieval import RetrievalService


@pytest.mark.asyncio
async def test_search_returns_retrieval_hits(monkeypatch: pytest.MonkeyPatch) -> None:
    chunk_id = uuid4()
    document_id = uuid4()
    chunk = SimpleNamespace(
        id=chunk_id,
        document_id=document_id,
        content="retrieved context",
        metadata_={"source": "knowledge.md"},
    )
    document = SimpleNamespace(id=document_id, filename="knowledge.md")
    db = SimpleNamespace(
        execute=lambda stmt: SimpleNamespace(all=lambda: [(chunk, document, 0.123)]),  # noqa: ARG005
    )

    async def fake_embed(self, texts: list[str]) -> list[list[float]]:  # noqa: ARG001
        assert texts == ["how to deploy"]
        return [[0.1, 0.2, 0.3]]

    monkeypatch.setattr("app.services.llm_client.OpenAICompatibleClient.embed", fake_embed)
    monkeypatch.setattr(
        "app.services.retrieval.get_retrieval_cache",
        lambda: SimpleNamespace(
            get_search_hits=lambda _query, _top_k: None,
            set_search_hits=lambda _query, _top_k, _hits: None,
        ),
    )

    response = await RetrievalService(db).search("how to deploy", top_k=3, request_id="req-1")
    hits = response.hits

    assert len(hits) == 1
    assert hits[0].chunk_id == chunk_id
    assert hits[0].document_id == document_id
    assert hits[0].filename == "knowledge.md"
    assert hits[0].content == "retrieved context"
    assert hits[0].metadata == {"source": "knowledge.md"}
    assert hits[0].score == 0.123
    assert response.query == "how to deploy"
    assert response.meta.request_id == "req-1"
    assert response.meta.cache_hit is False


@pytest.mark.asyncio
async def test_search_returns_cached_hits_without_embedding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cached_hit = RetrievalHit(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename="cached.md",
        content="cached context",
        score=0.02,
        metadata={"source": "cached.md"},
    )
    cache = SimpleNamespace(
        get_search_hits=lambda query, top_k: (
            [cached_hit] if (query, top_k) == ("cached", 2) else None
        ),
        set_search_hits=lambda _query, _top_k, _hits: None,
    )

    async def fake_embed(self, texts: list[str]) -> list[list[float]]:  # noqa: ARG001
        raise AssertionError("embed should not be called on cache hit")

    monkeypatch.setattr("app.services.retrieval.get_retrieval_cache", lambda: cache)
    monkeypatch.setattr("app.services.llm_client.OpenAICompatibleClient.embed", fake_embed)

    response = await RetrievalService(db=SimpleNamespace()).search(
        "cached",
        top_k=2,
        request_id="req-cache",
    )

    assert response.hits == [cached_hit]
    assert response.meta.request_id == "req-cache"
    assert response.meta.cache_hit is True
