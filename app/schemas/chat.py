from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    system_prompt: str | None = None


class ChatSource(BaseModel):
    filename: str
    content: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
