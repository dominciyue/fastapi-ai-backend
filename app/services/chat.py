from collections.abc import AsyncGenerator
from time import perf_counter

from sqlalchemy.orm import Session

from app.schemas.chat import ChatMeta, ChatResponse, ChatSource, TokenUsage
from app.services.llm_client import OpenAICompatibleClient
from app.services.retrieval import RetrievalService


class ChatService:
    def __init__(self, db: Session) -> None:
        self.retrieval = RetrievalService(db)
        self.client = OpenAICompatibleClient()

    def _estimate_token_usage(self, prompt: str, answer: str) -> TokenUsage:
        prompt_tokens = max(1, len(prompt.split()))
        completion_tokens = max(1, len(answer.split()))
        return TokenUsage(
            prompt_tokens_estimate=prompt_tokens,
            completion_tokens_estimate=completion_tokens,
            total_tokens_estimate=prompt_tokens + completion_tokens,
        )

    async def answer(
        self,
        query: str,
        top_k: int,
        system_prompt: str | None,
        request_id: str = "unknown",
        rerank: bool | None = None,
    ) -> ChatResponse:
        started_at = perf_counter()
        retrieval_response = await self.retrieval.search(
            query,
            top_k,
            request_id=request_id,
            rerank=rerank,
        )
        hits = retrieval_response.hits
        context = "\n\n".join(f"[{idx + 1}] {hit.content}" for idx, hit in enumerate(hits))
        prompt = (
            "Use the context below to answer the user.\n"
            "If the context is insufficient, say so clearly.\n\n"
            f"Context:\n{context}\n\nQuestion: {query}"
        )
        answer = await self.client.chat(prompt, system_prompt=system_prompt)
        latency_ms = int((perf_counter() - started_at) * 1000)
        sources = [
            ChatSource(
                filename=hit.filename,
                content=hit.content,
                score=hit.score,
            )
            for hit in hits
        ]
        return ChatResponse(
            answer=answer,
            sources=sources,
            meta=ChatMeta(
                request_id=request_id,
                latency_ms=latency_ms,
                retrieval_cache_hit=retrieval_response.meta.cache_hit,
                retrieval_reranked=retrieval_response.meta.reranked,
                retrieval_candidate_count=retrieval_response.meta.candidate_count,
                token_usage=self._estimate_token_usage(prompt, answer),
            ),
        )

    async def stream_answer(
        self,
        query: str,
        top_k: int,
        system_prompt: str | None,
        request_id: str = "unknown",
        rerank: bool | None = None,
    ) -> tuple[list[ChatSource], AsyncGenerator[str, None]]:
        retrieval_response = await self.retrieval.search(
            query,
            top_k,
            request_id=request_id,
            rerank=rerank,
        )
        hits = retrieval_response.hits
        context = "\n\n".join(f"[{idx + 1}] {hit.content}" for idx, hit in enumerate(hits))
        prompt = (
            "Use the context below to answer the user.\n"
            "If the context is insufficient, say so clearly.\n\n"
            f"Context:\n{context}\n\nQuestion: {query}"
        )
        sources = [
            ChatSource(
                filename=hit.filename,
                content=hit.content,
                score=hit.score,
            )
            for hit in hits
        ]
        return sources, self.client.stream_chat(prompt, system_prompt=system_prompt)
