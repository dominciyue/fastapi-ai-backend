from app.core.metrics import MetricsStore


def test_metrics_store_snapshot_aggregates_http_retrieval_and_chat_stats() -> None:
    store = MetricsStore()

    store.record_http_request("/health", 200, 12)
    store.record_http_request("/api/v1/chat/query", 502, 30)
    store.record_retrieval(cache_hit=True, reranked=True)
    store.record_retrieval(cache_hit=False, reranked=False)
    store.record_chat(
        streamed=False,
        prompt_tokens_estimate=40,
        completion_tokens_estimate=12,
        context_characters=320,
        context_truncated=True,
    )
    store.record_chat(
        streamed=True,
        prompt_tokens_estimate=25,
        completion_tokens_estimate=10,
        context_characters=180,
        context_truncated=False,
    )

    snapshot = store.snapshot()

    assert snapshot["http"]["total_requests"] == 2
    assert snapshot["http"]["total_errors"] == 1
    assert snapshot["retrieval"]["cache_hits"] == 1
    assert snapshot["retrieval"]["cache_misses"] == 1
    assert snapshot["retrieval"]["rerank_requests"] == 1
    assert snapshot["chat"]["total_requests"] == 2
    assert snapshot["chat"]["streamed_requests"] == 1
    assert snapshot["chat"]["total_prompt_tokens_estimate"] == 65
    assert snapshot["chat"]["total_completion_tokens_estimate"] == 22
    assert snapshot["chat"]["total_token_estimate"] == 87
    assert snapshot["chat"]["context_truncations"] == 1
    assert snapshot["chat"]["average_context_characters"] == 250.0


def test_metrics_store_reset_clears_all_counters() -> None:
    store = MetricsStore()
    store.record_http_request("/health", 200, 10)
    store.record_retrieval(cache_hit=True, reranked=True)
    store.record_chat(
        streamed=True,
        prompt_tokens_estimate=10,
        completion_tokens_estimate=5,
        context_characters=100,
        context_truncated=True,
    )

    store.reset()
    snapshot = store.snapshot()

    assert snapshot["http"]["total_requests"] == 0
    assert snapshot["retrieval"]["cache_hits"] == 0
    assert snapshot["chat"]["total_requests"] == 0
    assert snapshot["chat"]["context_truncations"] == 0
