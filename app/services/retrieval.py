from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Document, DocumentChunk
from app.schemas.retrieval import RetrievalHit
from app.services.llm_client import OpenAICompatibleClient


class RetrievalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.client = OpenAICompatibleClient()
        self.settings = get_settings()

    async def search(self, query: str, top_k: int | None = None) -> list[RetrievalHit]:
        requested_top_k = top_k or self.settings.retrieval_top_k
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
        return [
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
