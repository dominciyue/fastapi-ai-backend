# 可观测性

## 目标

当前项目没有接入完整 tracing / metrics 平台，但已经提供了一组轻量级可观测性能力，用于支持：

- 联调排障
- 演示时的状态确认
- 上层平台对调用链路的基本感知

## 请求级追踪

服务会自动为每次请求生成或透传 `request_id`。

行为如下：

- 如果调用方传入 `X-Request-ID`，服务会沿用该值
- 如果调用方未传入，服务会自动生成一个新的 UUID

最终该值会出现在：

- 响应头 `x-request-id`
- 业务返回体的 `meta.request_id`
- 错误返回体的 `request_id`

这让调用方可以用同一个 ID 关联：

- 上下游日志
- 客户端错误提示
- 手工排查过程

## 响应耗时

服务会在响应头返回：

- `x-response-time-ms`

该字段表示服务端处理耗时，适合用于：

- 快速观察接口是否明显变慢
- 对比缓存命中和缓存未命中的差异
- 演示时说明链路开销

## 健康检查

### `GET /health`

用于确认 API 进程是否存活。

### `GET /health/ready`

用于确认服务依赖是否就绪，包括：

- PostgreSQL
- Redis

如果依赖不可用，该接口会返回 `503`。

## `/metrics`

`GET /metrics` 会返回当前进程内的轻量聚合统计。

### HTTP 维度

- `total_requests`
- `total_errors`
- `average_latency_ms`
- `requests_by_path`
- `requests_by_status`

### Retrieval 维度

- `cache_hits`
- `cache_misses`
- `rerank_requests`

### Chat 维度

- `total_requests`
- `streamed_requests`
- `total_prompt_tokens_estimate`
- `total_completion_tokens_estimate`
- `total_token_estimate`
- `average_context_characters`
- `context_truncations`

## 调用方可感知的 warnings

除了 metrics 之外，当前服务也会在业务响应中显式返回 warnings，用于提示“本次请求虽然成功，但存在需要关注的降级信号”。

### Retrieval warnings

可能包括：

- `No retrieval hits matched the current query.`
- `Retrieval returned fewer hits than requested.`

### Chat warnings

可能包括：

- `Retrieval returned fewer hits than requested.`
- `Context was truncated to fit the configured character limit.`
- `Answer was generated without retrieval hits.`

这类字段对 `Dify` 或其他外部系统非常有用，因为它们能让上层系统显式感知服务降级，而不是只拿到一个“看起来成功”的结果。

## 当前边界

当前可观测性实现属于轻量级工程版本，尚未覆盖：

- Prometheus 指标暴露
- OpenTelemetry tracing
- 分布式链路跟踪
- 日志聚合平台
- 告警系统

如果后续进入更接近生产化的阶段，这些能力可以在当前基础上继续扩展。
