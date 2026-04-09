from uuid import uuid4

import pytest

from app.core.metrics import metrics_store
from app.schemas.retrieval import RetrievalHit, RetrievalMeta, RetrievalResponse
from app.services.chat import ChatService


def _sample_hits() -> list[RetrievalHit]:
    return [
        RetrievalHit(
            chunk_id=uuid4(),
            document_id=uuid4(),
            filename="guide.md",
            content="First retrieved chunk.",
            score=0.11,
            metadata={"source": "guide.md"},
        ),
        RetrievalHit(
            chunk_id=uuid4(),
            document_id=uuid4(),
            filename="faq.md",
            content="Second retrieved chunk.",
            score=0.22,
            metadata={"source": "faq.md"},
        ),
    ]


@pytest.mark.asyncio
async def test_answer_builds_prompt_and_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str | None] = {}

    async def fake_search(
        self,
        query: str,
        top_k: int,
        request_id: str = "unknown",
        rerank: bool | None = None,
    ) -> RetrievalResponse:  # noqa: ARG001
        assert query == "What can this service do?"
        assert top_k == 2
        assert request_id == "req-123"
        assert rerank is True
        return RetrievalResponse(
            query=query,
            hits=_sample_hits(),
            meta=RetrievalMeta(
                request_id=request_id,
                latency_ms=8,
                cache_hit=True,
                reranked=True,
                candidate_count=4,
                warnings=[],
            ),
        )

    async def fake_chat(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
    ) -> str:  # noqa: ARG001
        captured["prompt"] = prompt
        captured["system_prompt"] = system_prompt
        captured["max_tokens"] = str(max_tokens)
        return "It supports retrieval and chat."

    monkeypatch.setattr("app.services.retrieval.RetrievalService.search", fake_search)
    monkeypatch.setattr("app.services.llm_client.OpenAICompatibleClient.chat", fake_chat)

    response = await ChatService(db=None).answer(
        "What can this service do?",
        top_k=2,
        system_prompt="answer briefly",
        request_id="req-123",
        rerank=True,
        max_context_characters=40,
        max_answer_tokens=120,
    )

    assert response.answer == "It supports retrieval and chat."
    assert [source.filename for source in response.sources] == ["guide.md", "faq.md"]
    assert "[1] First retrieved chunk." in str(captured["prompt"])
    assert "Question: What can this service do?" in str(captured["prompt"])
    assert captured["system_prompt"] == "answer briefly"
    assert captured["max_tokens"] == "120"
    assert response.meta.request_id == "req-123"
    assert response.meta.retrieval_cache_hit is True
    assert response.meta.retrieval_reranked is True
    assert response.meta.retrieval_candidate_count == 4
    assert response.meta.context_characters <= 40
    assert response.meta.context_truncated is True
    assert response.meta.answer_max_tokens == 120
    assert "Context was truncated" in " ".join(response.meta.warnings)
    assert response.meta.token_usage.total_tokens_estimate >= 2
    metrics = metrics_store.snapshot()
    assert metrics["chat"]["total_requests"] == 1
    assert metrics["chat"]["streamed_requests"] == 0
    assert metrics["chat"]["context_truncations"] == 1


@pytest.mark.asyncio
async def test_stream_answer_returns_sources_and_generator(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str | None] = {}

    async def fake_search(
        self,
        query: str,
        top_k: int,
        request_id: str = "unknown",
        rerank: bool | None = None,
    ) -> RetrievalResponse:  # noqa: ARG001
        assert query == "Stream a response"
        assert top_k == 1
        assert request_id == "req-stream"
        assert rerank is False
        return RetrievalResponse(
            query=query,
            hits=_sample_hits()[:1],
            meta=RetrievalMeta(
                request_id=request_id,
                latency_ms=5,
                cache_hit=False,
                reranked=False,
                candidate_count=1,
                warnings=["Retrieval returned fewer hits than requested."],
            ),
        )

    async def fake_stream_chat(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
    ):  # noqa: ARG001
        captured["prompt"] = prompt
        captured["system_prompt"] = system_prompt
        captured["max_tokens"] = str(max_tokens)
        for token in ["token-1 ", "token-2"]:
            yield token

    monkeypatch.setattr("app.services.retrieval.RetrievalService.search", fake_search)
    monkeypatch.setattr(
        "app.services.llm_client.OpenAICompatibleClient.stream_chat",
        fake_stream_chat,
    )

    sources, generator = await ChatService(db=None).stream_answer(
        "Stream a response",
        top_k=1,
        system_prompt=None,
        request_id="req-stream",
        rerank=False,
        max_context_characters=80,
        max_answer_tokens=64,
    )
    chunks = [chunk async for chunk in generator]

    assert len(sources) == 1
    assert sources[0].filename == "guide.md"
    assert chunks == ["token-1 ", "token-2"]
    assert "[1] First retrieved chunk." in str(captured["prompt"])
    assert captured["system_prompt"] is None
    assert captured["max_tokens"] == "64"
    metrics = metrics_store.snapshot()
    assert metrics["chat"]["total_requests"] == 1
    assert metrics["chat"]["streamed_requests"] == 1
