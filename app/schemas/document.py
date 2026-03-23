from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    content_type: str
    status: str
    chunk_count: int
    created_at: datetime


class UploadResponse(BaseModel):
    document: DocumentResponse
    message: str = "Document uploaded successfully."


class IndexRequest(BaseModel):
    document_id: UUID
    metadata: dict = Field(default_factory=dict)
