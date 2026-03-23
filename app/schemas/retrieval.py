from uuid import UUID

from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievalHit(BaseModel):
    chunk_id: UUID
    document_id: UUID
    filename: str
    content: str
    score: float
    metadata: dict


class RetrievalResponse(BaseModel):
    query: str
    hits: list[RetrievalHit]
