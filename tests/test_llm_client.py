import pytest

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.services.llm_client import OpenAICompatibleClient


@pytest.mark.asyncio
async def test_mock_embed_is_deterministic() -> None:
    settings = get_settings()
    original_openai_api_key = settings.openai_api_key
    original_embedding_api_key = settings.embedding_api_key
    settings.openai_api_key = ""
    settings.embedding_api_key = ""

    client = OpenAICompatibleClient()
    try:
        first = await client.embed(["hello world"])
        second = await client.embed(["hello world"])
    finally:
        settings.openai_api_key = original_openai_api_key
        settings.embedding_api_key = original_embedding_api_key

    assert len(first) == 1
    assert len(first[0]) == settings.embedding_dimension
    assert first == second


@pytest.mark.asyncio
async def test_mock_chat_and_stream_return_demo_text() -> None:
    settings = get_settings()
    original_openai_api_key = settings.openai_api_key
    original_chat_api_key = settings.chat_api_key
    settings.openai_api_key = ""
    settings.chat_api_key = ""

    client = OpenAICompatibleClient()
    try:
        answer = await client.chat("Summarize the current context.")
        chunks = [chunk async for chunk in client.stream_chat("Summarize the current context.")]
    finally:
        settings.openai_api_key = original_openai_api_key
        settings.chat_api_key = original_chat_api_key

    assert "Local demo mode" in answer
    assert chunks
    assert "Local demo mode" in "".join(chunks)


def test_chat_and_embedding_settings_can_be_split() -> None:
    settings = get_settings()
    original_openai_base_url = settings.openai_base_url
    original_openai_api_key = settings.openai_api_key
    original_chat_base_url = settings.chat_base_url
    original_chat_api_key = settings.chat_api_key
    original_embedding_base_url = settings.embedding_base_url
    original_embedding_api_key = settings.embedding_api_key

    settings.openai_base_url = "https://openai.example/v1"
    settings.openai_api_key = "openai-key"
    settings.chat_base_url = "https://chat.example/v1"
    settings.chat_api_key = "chat-key"
    settings.embedding_base_url = "https://embedding.example/v1"
    settings.embedding_api_key = "embedding-key"

    try:
        client = OpenAICompatibleClient()
        assert client._chat_base_url == "https://chat.example/v1"
        assert client._chat_api_key == "chat-key"
        assert client._embedding_base_url == "https://embedding.example/v1"
        assert client._embedding_api_key == "embedding-key"
    finally:
        settings.openai_base_url = original_openai_base_url
        settings.openai_api_key = original_openai_api_key
        settings.chat_base_url = original_chat_base_url
        settings.chat_api_key = original_chat_api_key
        settings.embedding_base_url = original_embedding_base_url
        settings.embedding_api_key = original_embedding_api_key


def test_chat_and_embedding_settings_fall_back_to_openai_defaults() -> None:
    settings = get_settings()
    original_openai_base_url = settings.openai_base_url
    original_openai_api_key = settings.openai_api_key
    original_chat_base_url = settings.chat_base_url
    original_chat_api_key = settings.chat_api_key
    original_embedding_base_url = settings.embedding_base_url
    original_embedding_api_key = settings.embedding_api_key

    settings.openai_base_url = "https://openai.example/v1"
    settings.openai_api_key = "openai-key"
    settings.chat_base_url = ""
    settings.chat_api_key = ""
    settings.embedding_base_url = ""
    settings.embedding_api_key = ""

    try:
        client = OpenAICompatibleClient()
        assert client._chat_base_url == "https://openai.example/v1"
        assert client._chat_api_key == "openai-key"
        assert client._embedding_base_url == "https://openai.example/v1"
        assert client._embedding_api_key == "openai-key"
    finally:
        settings.openai_base_url = original_openai_base_url
        settings.openai_api_key = original_openai_api_key
        settings.chat_base_url = original_chat_base_url
        settings.chat_api_key = original_chat_api_key
        settings.embedding_base_url = original_embedding_base_url
        settings.embedding_api_key = original_embedding_api_key


def test_validate_embedding_dimensions_raises_on_mismatch() -> None:
    settings = get_settings()
    original_dimension = settings.embedding_dimension
    settings.embedding_dimension = 1536

    try:
        client = OpenAICompatibleClient()
        with pytest.raises(AppError, match="Embedding dimension mismatch"):
            client._validate_embedding_dimensions([[0.1] * 1024])
    finally:
        settings.embedding_dimension = original_dimension
