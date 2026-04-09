from time import perf_counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Document, DocumentChunk
from app.schemas.retrieval import RetrievalHit, RetrievalMeta, RetrievalResponse
from app.services.cache import get_retrieval_cache
from app.services.llm_client import OpenAICompatibleClient


class RetrievalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.client = OpenAICompatibleClient()
        self.cache = get_retrieval_cache()
        self.settings = get_settings()

    async def search(
        self, query: str, top_k: int | None = None, request_id: str = "unknown"
    ) -> RetrievalResponse:
        started_at = perf_counter()
        requested_top_k = top_k or self.settings.retrieval_top_k
        cached_hits = self.cache.get_search_hits(query, requested_top_k)
        if cached_hits is not None:
            latency_ms = int((perf_counter() - started_at) * 1000)
            return RetrievalResponse(
                query=query,
                hits=cached_hits,
                meta=RetrievalMeta(request_id=request_id, latency_ms=latency_ms, cache_hit=True),
            )

        query_embedding = (await self.client.embed([query]))[0]
        stmt = (
            select(
                DocumentChunk,
                Document,
                DocumentChunk.embedding.cosine_distance(query_embedding).label("score"),
            )
            .join(Document, Document.id == DocumentChunk.document_id)
            .order_by("score")
            .limit(requested_top_k)
        )
        results = self.db.execute(stmt).all()
        hits = [
            RetrievalHit(
                chunk_id=chunk.id,
                document_id=document.id,
                filename=document.filename,
                content=chunk.content,
                score=float(score),
                metadata=chunk.metadata_,
            )
            for chunk, document, score in results
        ]
        self.cache.set_search_hits(query, requested_top_k, hits)
        latency_ms = int((perf_counter() - started_at) * 1000)
        return RetrievalResponse(
            query=query,
            hits=hits,
            meta=RetrievalMeta(request_id=request_id, latency_ms=latency_ms, cache_hit=False),
        )
