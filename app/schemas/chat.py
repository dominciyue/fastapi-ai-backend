from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    system_prompt: str | None = None


class ChatSource(BaseModel):
    filename: str
    content: str
    score: float


class TokenUsage(BaseModel):
    prompt_tokens_estimate: int
    completion_tokens_estimate: int
    total_tokens_estimate: int


class ChatMeta(BaseModel):
    request_id: str
    latency_ms: int
    retrieval_cache_hit: bool
    token_usage: TokenUsage


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
    meta: ChatMeta
