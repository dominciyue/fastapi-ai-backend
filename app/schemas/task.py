from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    status: str
    detail: str | None = None
    created_at: datetime
    updated_at: datetime
