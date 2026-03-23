import pytest

from app.core.config import get_settings
from app.services.llm_client import OpenAICompatibleClient


@pytest.mark.asyncio
async def test_mock_embed_is_deterministic() -> None:
    settings = get_settings()
    original_api_key = settings.openai_api_key
    settings.openai_api_key = ""

    client = OpenAICompatibleClient()
    try:
        first = await client.embed(["hello world"])
        second = await client.embed(["hello world"])
    finally:
        settings.openai_api_key = original_api_key

    assert len(first) == 1
    assert len(first[0]) == settings.embedding_dimension
    assert first == second


@pytest.mark.asyncio
async def test_mock_chat_and_stream_return_demo_text() -> None:
    settings = get_settings()
    original_api_key = settings.openai_api_key
    settings.openai_api_key = ""

    client = OpenAICompatibleClient()
    try:
        answer = await client.chat("Summarize the current context.")
        chunks = [chunk async for chunk in client.stream_chat("Summarize the current context.")]
    finally:
        settings.openai_api_key = original_api_key

    assert "Local demo mode" in answer
    assert chunks
    assert "Local demo mode" in "".join(chunks)
