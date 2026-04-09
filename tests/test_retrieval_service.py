from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.metrics import metrics_store
from app.schemas.retrieval import RetrievalHit
from app.services.retrieval import RetrievalService


@pytest.mark.asyncio
async def test_search_returns_retrieval_hits(monkeypatch: pytest.MonkeyPatch) -> None:
    metrics_store.reset()
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
            get_search_hits=lambda _query, _top_k, _rerank: None,
            set_search_hits=lambda _query, _top_k, _rerank, _hits: None,
        ),
    )

    response = await RetrievalService(db).search(
        "how to deploy",
        top_k=3,
        request_id="req-1",
        rerank=False,
    )
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
    assert response.meta.reranked is False
    assert response.meta.candidate_count == 1


@pytest.mark.asyncio
async def test_search_returns_cached_hits_without_embedding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics_store.reset()
    cached_hit = RetrievalHit(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename="cached.md",
        content="cached context",
        score=0.02,
        metadata={"source": "cached.md"},
    )
    cache = SimpleNamespace(
        get_search_hits=lambda query, top_k, rerank: (
            [cached_hit] if (query, top_k, rerank) == ("cached", 2, True) else None
        ),
        set_search_hits=lambda _query, _top_k, _rerank, _hits: None,
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
    assert response.meta.reranked is True
    assert response.meta.candidate_count == 1
    assert metrics_store.snapshot()["retrieval"]["cache_hits"] == 1


@pytest.mark.asyncio
async def test_search_reranks_hits_by_keyword_overlap(monkeypatch: pytest.MonkeyPatch) -> None:
    metrics_store.reset()
    chunk_a = SimpleNamespace(
        id=uuid4(),
        document_id=uuid4(),
        content="This paragraph mentions deployment steps and deployment workflow.",
        metadata_={"source": "deploy.md"},
    )
    chunk_b = SimpleNamespace(
        id=uuid4(),
        document_id=uuid4(),
        content="Generic project introduction without the target keyword.",
        metadata_={"source": "intro.md"},
    )
    document_a = SimpleNamespace(id=chunk_a.document_id, filename="deploy.md")
    document_b = SimpleNamespace(id=chunk_b.document_id, filename="intro.md")
    db = SimpleNamespace(
        execute=lambda stmt: SimpleNamespace(  # noqa: ARG005
            all=lambda: [(chunk_b, document_b, 0.01), (chunk_a, document_a, 0.02)]
        ),
    )
    settings = SimpleNamespace(
        retrieval_top_k=1,
        enable_keyword_rerank=True,
        rerank_candidate_multiplier=3,
    )

    async def fake_embed(self, texts: list[str]) -> list[list[float]]:  # noqa: ARG001
        return [[0.1, 0.2, 0.3]]

    monkeypatch.setattr("app.services.llm_client.OpenAICompatibleClient.embed", fake_embed)
    monkeypatch.setattr("app.services.retrieval.get_settings", lambda: settings)
    monkeypatch.setattr(
        "app.services.retrieval.get_retrieval_cache",
        lambda: SimpleNamespace(
            get_search_hits=lambda _query, _top_k, _rerank: None,
            set_search_hits=lambda _query, _top_k, _rerank, _hits: None,
        ),
    )

    response = await RetrievalService(db).search(
        "deployment",
        top_k=1,
        request_id="req-rerank",
        rerank=True,
    )

    assert response.hits[0].filename == "deploy.md"
    assert response.meta.reranked is True
    assert response.meta.candidate_count == 2
    metrics = metrics_store.snapshot()
    assert metrics["retrieval"]["cache_misses"] == 1
    assert metrics["retrieval"]["rerank_requests"] == 1
