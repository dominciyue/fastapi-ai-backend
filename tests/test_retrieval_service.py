from types import SimpleNamespace
from uuid import uuid4

import pytest

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

    hits = await RetrievalService(db).search("how to deploy", top_k=3)

    assert len(hits) == 1
    assert hits[0].chunk_id == chunk_id
    assert hits[0].document_id == document_id
    assert hits[0].filename == "knowledge.md"
    assert hits[0].content == "retrieved context"
    assert hits[0].metadata == {"source": "knowledge.md"}
    assert hits[0].score == 0.123
