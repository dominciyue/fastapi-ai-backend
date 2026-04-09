import json
import math
from collections.abc import AsyncGenerator
from hashlib import sha256

import httpx

from app.core.config import get_settings
from app.core.exceptions import AppError


class OpenAICompatibleClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def _chat_base_url(self) -> str:
        return self.settings.chat_base_url.strip() or self.settings.openai_base_url

    @property
    def _chat_api_key(self) -> str:
        return self.settings.chat_api_key.strip() or self.settings.openai_api_key.strip()

    @property
    def _embedding_base_url(self) -> str:
        return self.settings.embedding_base_url.strip() or self.settings.openai_base_url

    @property
    def _embedding_api_key(self) -> str:
        return self.settings.embedding_api_key.strip() or self.settings.openai_api_key.strip()

    def _use_mock_chat_mode(self) -> bool:
        return not self._chat_api_key

    def _use_mock_embedding_mode(self) -> bool:
        return not self._embedding_api_key

    def _mock_embedding(self, text: str) -> list[float]:
        values: list[float] = []
        counter = 0
        while len(values) < self.settings.embedding_dimension:
            digest = sha256(f"{text}:{counter}".encode()).digest()
            for idx in range(0, len(digest), 4):
                if len(values) >= self.settings.embedding_dimension:
                    break
                chunk = digest[idx : idx + 4]
                number = int.from_bytes(chunk, "big", signed=False) / (2**32)
                values.append((number * 2) - 1)
            counter += 1

        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        return [value / norm for value in values]

    def _mock_answer(self, prompt: str) -> str:
        preview = prompt[:500]
        return (
            "Local demo mode is enabled because no model API key was provided. "
            "Retrieval and context assembly succeeded. The response below is a mock answer "
            "generated from the current context:\n\n"
            f"{preview}"
        )

    def _headers(self, api_key: str) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _validate_embedding_dimensions(self, embeddings: list[list[float]]) -> list[list[float]]:
        for embedding in embeddings:
            actual_dimension = len(embedding)
            if actual_dimension != self.settings.embedding_dimension:
                raise AppError(
                    "Embedding dimension mismatch: "
                    f"configured EMBEDDING_DIMENSION={self.settings.embedding_dimension}, "
                    f"but provider returned {actual_dimension}. "
                    "Update EMBEDDING_DIMENSION to match the provider, then recreate or migrate "
                    "the pgvector schema before re-indexing.",
                    status_code=502,
                )
        return embeddings

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if self._use_mock_embedding_mode():
            return [self._mock_embedding(text) for text in texts]

        payload = {"model": self.settings.embedding_model, "input": texts}
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            response = await client.post(
                f"{self._embedding_base_url}/embeddings",
                headers=self._headers(self._embedding_api_key),
                json=payload,
            )
        if response.is_error:
            detail = response.text.strip() or "empty response body"
            if response.status_code == 404:
                detail = (
                    f"{detail}. The configured provider may not expose an /embeddings endpoint "
                    "or the embedding model may not exist."
                )
            raise AppError(
                f"Embedding request failed ({response.status_code}): {detail}",
                status_code=502,
            )
        data = response.json()["data"]
        return self._validate_embedding_dimensions([item["embedding"] for item in data])

    async def chat(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
    ) -> str:
        if self._use_mock_chat_mode():
            return self._mock_answer(prompt)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.settings.chat_model, "messages": messages, "stream": False}
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            response = await client.post(
                f"{self._chat_base_url}/chat/completions",
                headers=self._headers(self._chat_api_key),
                json=payload,
            )
        if response.is_error:
            raise AppError(f"Chat request failed: {response.text}", status_code=502)
        return response.json()["choices"][0]["message"]["content"]

    async def stream_chat(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[str, None]:
        if self._use_mock_chat_mode():
            answer = self._mock_answer(prompt)
            for token in answer.split():
                yield token + " "
            return

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.settings.chat_model, "messages": messages, "stream": True}
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self._chat_base_url}/chat/completions",
                headers=self._headers(self._chat_api_key),
                json=payload,
            ) as response:
                if response.is_error:
                    text = await response.aread()
                    raise AppError(f"Streaming chat failed: {text.decode()}", status_code=502)
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    payload = json.loads(data)
                    delta = payload["choices"][0]["delta"].get("content")
                    if delta:
                        yield delta
