from uuid import uuid4

import pytest

from app.schemas.retrieval import RetrievalHit
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

    async def fake_search(self, query: str, top_k: int) -> list[RetrievalHit]:  # noqa: ARG001
        assert query == "What can this service do?"
        assert top_k == 2
        return _sample_hits()

    async def fake_chat(self, prompt: str, system_prompt: str | None = None) -> str:  # noqa: ARG001
        captured["prompt"] = prompt
        captured["system_prompt"] = system_prompt
        return "It supports retrieval and chat."

    monkeypatch.setattr("app.services.retrieval.RetrievalService.search", fake_search)
    monkeypatch.setattr("app.services.llm_client.OpenAICompatibleClient.chat", fake_chat)

    response = await ChatService(db=None).answer(
        "What can this service do?",
        top_k=2,
        system_prompt="answer briefly",
    )

    assert response.answer == "It supports retrieval and chat."
    assert [source.filename for source in response.sources] == ["guide.md", "faq.md"]
    assert "[1] First retrieved chunk." in str(captured["prompt"])
    assert "[2] Second retrieved chunk." in str(captured["prompt"])
    assert "Question: What can this service do?" in str(captured["prompt"])
    assert captured["system_prompt"] == "answer briefly"


@pytest.mark.asyncio
async def test_stream_answer_returns_sources_and_generator(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str | None] = {}

    async def fake_search(self, query: str, top_k: int) -> list[RetrievalHit]:  # noqa: ARG001
        assert query == "Stream a response"
        assert top_k == 1
        return _sample_hits()[:1]

    async def fake_stream_chat(self, prompt: str, system_prompt: str | None = None):  # noqa: ARG001
        captured["prompt"] = prompt
        captured["system_prompt"] = system_prompt
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
    )
    chunks = [chunk async for chunk in generator]

    assert len(sources) == 1
    assert sources[0].filename == "guide.md"
    assert chunks == ["token-1 ", "token-2"]
    assert "[1] First retrieved chunk." in str(captured["prompt"])
    assert captured["system_prompt"] is None
