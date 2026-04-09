import re
from time import perf_counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.metrics import metrics_store
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

    def _tokenize(self, text: str) -> set[str]:
        return {token for token in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(token) >= 2}

    def _rerank_hits(self, query: str, hits: list[RetrievalHit], top_k: int) -> list[RetrievalHit]:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return hits[:top_k]

        def rerank_key(hit: RetrievalHit) -> tuple[int, float]:
            hit_tokens = self._tokenize(f"{hit.filename} {hit.content}")
            overlap = len(query_tokens & hit_tokens)
            return (overlap, -hit.score)

        return sorted(hits, key=rerank_key, reverse=True)[:top_k]

    async def search(
        self,
        query: str,
        top_k: int | None = None,
        request_id: str = "unknown",
        rerank: bool | None = None,
    ) -> RetrievalResponse:
        started_at = perf_counter()
        requested_top_k = top_k or self.settings.retrieval_top_k
        should_rerank = self.settings.enable_keyword_rerank if rerank is None else rerank
        cached_hits = self.cache.get_search_hits(query, requested_top_k, should_rerank)
        if cached_hits is not None:
            latency_ms = int((perf_counter() - started_at) * 1000)
            metrics_store.record_retrieval(cache_hit=True, reranked=should_rerank)
            return RetrievalResponse(
                query=query,
                hits=cached_hits,
                meta=RetrievalMeta(
                    request_id=request_id,
                    latency_ms=latency_ms,
                    cache_hit=True,
                    reranked=should_rerank,
                    candidate_count=len(cached_hits),
                ),
            )

        query_embedding = (await self.client.embed([query]))[0]
        candidate_limit = requested_top_k
        if should_rerank:
            candidate_limit = requested_top_k * max(1, self.settings.rerank_candidate_multiplier)
        stmt = (
            select(
                DocumentChunk,
                Document,
                DocumentChunk.embedding.cosine_distance(query_embedding).label("score"),
            )
            .join(Document, Document.id == DocumentChunk.document_id)
            .order_by("score")
            .limit(candidate_limit)
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
        candidate_count = len(hits)
        final_hits = (
            self._rerank_hits(query, hits, requested_top_k)
            if should_rerank
            else hits[:requested_top_k]
        )
        self.cache.set_search_hits(query, requested_top_k, should_rerank, final_hits)
        latency_ms = int((perf_counter() - started_at) * 1000)
        metrics_store.record_retrieval(cache_hit=False, reranked=should_rerank)
        return RetrievalResponse(
            query=query,
            hits=final_hits,
            meta=RetrievalMeta(
                request_id=request_id,
                latency_ms=latency_ms,
                cache_hit=False,
                reranked=should_rerank,
                candidate_count=candidate_count,
            ),
        )
