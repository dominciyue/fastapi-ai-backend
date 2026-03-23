from collections.abc import AsyncGenerator

from sqlalchemy.orm import Session

from app.schemas.chat import ChatResponse, ChatSource
from app.services.llm_client import OpenAICompatibleClient
from app.services.retrieval import RetrievalService


class ChatService:
    def __init__(self, db: Session) -> None:
        self.retrieval = RetrievalService(db)
        self.client = OpenAICompatibleClient()

    async def answer(self, query: str, top_k: int, system_prompt: str | None) -> ChatResponse:
        hits = await self.retrieval.search(query, top_k)
        context = "\n\n".join(f"[{idx + 1}] {hit.content}" for idx, hit in enumerate(hits))
        prompt = (
            "Use the context below to answer the user.\n"
            "If the context is insufficient, say so clearly.\n\n"
            f"Context:\n{context}\n\nQuestion: {query}"
        )
        answer = await self.client.chat(prompt, system_prompt=system_prompt)
        sources = [
            ChatSource(
                filename=hit.filename,
                content=hit.content,
                score=hit.score,
            )
            for hit in hits
        ]
        return ChatResponse(answer=answer, sources=sources)

    async def stream_answer(
        self, query: str, top_k: int, system_prompt: str | None
    ) -> tuple[list[ChatSource], AsyncGenerator[str, None]]:
        hits = await self.retrieval.search(query, top_k)
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
