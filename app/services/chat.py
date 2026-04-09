from collections.abc import AsyncGenerator
from time import perf_counter

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.metrics import metrics_store
from app.schemas.chat import ChatMeta, ChatResponse, ChatSource, TokenUsage
from app.services.llm_client import OpenAICompatibleClient
from app.services.retrieval import RetrievalService


class ChatService:
    def __init__(self, db: Session) -> None:
        self.retrieval = RetrievalService(db)
        self.client = OpenAICompatibleClient()
        self.settings = get_settings()

    def _estimate_token_usage(self, prompt: str, answer: str) -> TokenUsage:
        prompt_tokens = max(1, len(prompt.split()))
        completion_tokens = max(1, len(answer.split()))
        return TokenUsage(
            prompt_tokens_estimate=prompt_tokens,
            completion_tokens_estimate=completion_tokens,
            total_tokens_estimate=prompt_tokens + completion_tokens,
        )

    def _build_context(
        self,
        hits: list[ChatSource],
        max_context_characters: int,
    ) -> tuple[str, int, bool]:
        lines: list[str] = []
        total_characters = 0
        truncated = False

        for idx, hit in enumerate(hits):
            chunk = f"[{idx + 1}] {hit.content}"
            separator = "\n\n" if lines else ""
            next_total = total_characters + len(separator) + len(chunk)
            if next_total > max_context_characters:
                truncated = True
                remaining = max_context_characters - total_characters - len(separator)
                if remaining > 32:
                    chunk = chunk[:remaining].rstrip() + "..."
                    lines.append(chunk)
                    total_characters += len(separator) + len(chunk)
                break
            lines.append(chunk)
            total_characters = next_total

        return "\n\n".join(lines), total_characters, truncated

    async def answer(
        self,
        query: str,
        top_k: int,
        system_prompt: str | None,
        request_id: str = "unknown",
        rerank: bool | None = None,
        max_context_characters: int | None = None,
        max_answer_tokens: int | None = None,
    ) -> ChatResponse:
        started_at = perf_counter()
        retrieval_response = await self.retrieval.search(
            query,
            top_k,
            request_id=request_id,
            rerank=rerank,
        )
        hits = retrieval_response.hits
        sources = [
            ChatSource(
                filename=hit.filename,
                content=hit.content,
                score=hit.score,
            )
            for hit in hits
        ]
        context_limit = max_context_characters or self.settings.max_context_characters
        answer_limit = max_answer_tokens or self.settings.max_answer_tokens
        context, context_characters, context_truncated = self._build_context(sources, context_limit)
        prompt = (
            "Use the context below to answer the user.\n"
            "If the context is insufficient, say so clearly.\n\n"
            f"Context:\n{context}\n\nQuestion: {query}"
        )
        answer = await self.client.chat(
            prompt,
            system_prompt=system_prompt,
            max_tokens=answer_limit,
        )
        latency_ms = int((perf_counter() - started_at) * 1000)
        warnings = list(retrieval_response.meta.warnings)
        if context_truncated:
            warnings.append("Context was truncated to fit the configured character limit.")
        if not sources:
            warnings.append("Answer was generated without retrieval hits.")
        usage = self._estimate_token_usage(prompt, answer)
        metrics_store.record_chat(
            streamed=False,
            prompt_tokens_estimate=usage.prompt_tokens_estimate,
            completion_tokens_estimate=usage.completion_tokens_estimate,
            context_characters=context_characters,
            context_truncated=context_truncated,
        )
        return ChatResponse(
            answer=answer,
            sources=sources,
            meta=ChatMeta(
                request_id=request_id,
                latency_ms=latency_ms,
                retrieval_cache_hit=retrieval_response.meta.cache_hit,
                retrieval_reranked=retrieval_response.meta.reranked,
                retrieval_candidate_count=retrieval_response.meta.candidate_count,
                context_characters=context_characters,
                context_truncated=context_truncated,
                answer_max_tokens=answer_limit,
                warnings=warnings,
                token_usage=usage,
            ),
        )

    async def stream_answer(
        self,
        query: str,
        top_k: int,
        system_prompt: str | None,
        request_id: str = "unknown",
        rerank: bool | None = None,
        max_context_characters: int | None = None,
        max_answer_tokens: int | None = None,
    ) -> tuple[list[ChatSource], AsyncGenerator[str, None]]:
        retrieval_response = await self.retrieval.search(
            query,
            top_k,
            request_id=request_id,
            rerank=rerank,
        )
        hits = retrieval_response.hits
        sources = [
            ChatSource(
                filename=hit.filename,
                content=hit.content,
                score=hit.score,
            )
            for hit in hits
        ]
        context_limit = max_context_characters or self.settings.max_context_characters
        answer_limit = max_answer_tokens or self.settings.max_answer_tokens
        context, context_characters, context_truncated = self._build_context(sources, context_limit)
        prompt = (
            "Use the context below to answer the user.\n"
            "If the context is insufficient, say so clearly.\n\n"
            f"Context:\n{context}\n\nQuestion: {query}"
        )
        raw_generator = self.client.stream_chat(
            prompt,
            system_prompt=system_prompt,
            max_tokens=answer_limit,
        )

        async def tracked_generator() -> AsyncGenerator[str, None]:
            chunks: list[str] = []
            async for chunk in raw_generator:
                chunks.append(chunk)
                yield chunk
            usage = self._estimate_token_usage(prompt, "".join(chunks))
            metrics_store.record_chat(
                streamed=True,
                prompt_tokens_estimate=usage.prompt_tokens_estimate,
                completion_tokens_estimate=usage.completion_tokens_estimate,
                context_characters=context_characters,
                context_truncated=context_truncated,
            )

        return sources, tracked_generator()
