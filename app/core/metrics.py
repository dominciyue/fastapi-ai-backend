from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class MetricsStore:
    total_requests: int = 0
    total_errors: int = 0
    total_latency_ms: int = 0
    requests_by_path: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    requests_by_status: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    retrieval_cache_hits: int = 0
    retrieval_cache_misses: int = 0
    retrieval_rerank_requests: int = 0
    chat_requests: int = 0
    streamed_chat_requests: int = 0
    total_prompt_tokens_estimate: int = 0
    total_completion_tokens_estimate: int = 0
    total_context_characters: int = 0
    context_truncations: int = 0

    def record_http_request(self, path: str, status_code: int, latency_ms: int) -> None:
        self.total_requests += 1
        self.total_latency_ms += latency_ms
        self.requests_by_path[path] += 1
        self.requests_by_status[str(status_code)] += 1
        if status_code >= 400:
            self.total_errors += 1

    def record_retrieval(self, *, cache_hit: bool, reranked: bool) -> None:
        if cache_hit:
            self.retrieval_cache_hits += 1
        else:
            self.retrieval_cache_misses += 1
        if reranked:
            self.retrieval_rerank_requests += 1

    def record_chat(
        self,
        *,
        streamed: bool,
        prompt_tokens_estimate: int,
        completion_tokens_estimate: int,
        context_characters: int,
        context_truncated: bool,
    ) -> None:
        self.chat_requests += 1
        if streamed:
            self.streamed_chat_requests += 1
        self.total_prompt_tokens_estimate += prompt_tokens_estimate
        self.total_completion_tokens_estimate += completion_tokens_estimate
        self.total_context_characters += context_characters
        if context_truncated:
            self.context_truncations += 1

    def snapshot(self) -> dict[str, object]:
        average_latency_ms = 0.0
        if self.total_requests:
            average_latency_ms = round(self.total_latency_ms / self.total_requests, 2)

        average_context_characters = 0.0
        if self.chat_requests:
            average_context_characters = round(
                self.total_context_characters / self.chat_requests,
                2,
            )

        return {
            "http": {
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "average_latency_ms": average_latency_ms,
                "requests_by_path": dict(self.requests_by_path),
                "requests_by_status": dict(self.requests_by_status),
            },
            "retrieval": {
                "cache_hits": self.retrieval_cache_hits,
                "cache_misses": self.retrieval_cache_misses,
                "rerank_requests": self.retrieval_rerank_requests,
            },
            "chat": {
                "total_requests": self.chat_requests,
                "streamed_requests": self.streamed_chat_requests,
                "total_prompt_tokens_estimate": self.total_prompt_tokens_estimate,
                "total_completion_tokens_estimate": self.total_completion_tokens_estimate,
                "total_token_estimate": (
                    self.total_prompt_tokens_estimate
                    + self.total_completion_tokens_estimate
                ),
                "average_context_characters": average_context_characters,
                "context_truncations": self.context_truncations,
            },
        }

    def reset(self) -> None:
        self.total_requests = 0
        self.total_errors = 0
        self.total_latency_ms = 0
        self.requests_by_path.clear()
        self.requests_by_status.clear()
        self.retrieval_cache_hits = 0
        self.retrieval_cache_misses = 0
        self.retrieval_rerank_requests = 0
        self.chat_requests = 0
        self.streamed_chat_requests = 0
        self.total_prompt_tokens_estimate = 0
        self.total_completion_tokens_estimate = 0
        self.total_context_characters = 0
        self.context_truncations = 0


metrics_store = MetricsStore()
