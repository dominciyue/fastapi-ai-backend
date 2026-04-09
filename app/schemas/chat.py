from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    system_prompt: str | None = None
    rerank: bool | None = None
    max_context_characters: int | None = Field(default=None, ge=200, le=12000)
    max_answer_tokens: int | None = Field(default=None, ge=32, le=2048)


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
    retrieval_reranked: bool
    retrieval_candidate_count: int
    context_characters: int
    context_truncated: bool
    answer_max_tokens: int
    token_usage: TokenUsage


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
    meta: ChatMeta
