# API 说明

## 基础信息

- Base URL: `http://localhost:8000`
- API Prefix: `/api/v1`
- 在线文档：`http://localhost:8000/docs`
- OpenAPI 资产：`integrations/dify-tool.openapi.yaml`

## 通用响应头

服务会为每次请求返回：

- `x-request-id`
  - 请求链路标识，便于排查日志和上下游联调
- `x-response-time-ms`
  - 本次请求服务端处理耗时

## 核心接口

### 文档上传

- `POST /api/v1/documents/upload`

用于上传原始文档并写入本地存储。

### 创建索引任务

- `POST /api/v1/documents/index`

用于为已上传文档创建异步索引任务。

### 查询任务状态

- `GET /api/v1/tasks/{task_id}`

用于轮询索引任务状态。

### 检索

- `POST /api/v1/retrieval/search`

用于根据 query 返回最相关的文档片段。

请求体关键字段：

- `query`
- `top_k`
- `rerank`

响应除了 `hits` 以外，还会返回：

- `meta.request_id`
- `meta.latency_ms`
- `meta.cache_hit`
- `meta.reranked`
- `meta.candidate_count`
- `meta.warnings`

### 同步问答

- `POST /api/v1/chat/query`

用于返回最终答案与来源片段。

请求体关键字段：

- `query`
- `top_k`
- `system_prompt`
- `rerank`
- `max_context_characters`
- `max_answer_tokens`

响应除 `answer` 和 `sources` 外，还会返回：

- `meta.request_id`
- `meta.latency_ms`
- `meta.retrieval_cache_hit`
- `meta.retrieval_reranked`
- `meta.retrieval_candidate_count`
- `meta.context_characters`
- `meta.context_truncated`
- `meta.answer_max_tokens`
- `meta.warnings`
- `meta.token_usage`

### 流式问答

- `POST /api/v1/chat/stream`

返回 `text/event-stream`，适合原生前端、自定义脚本和直接消费 `SSE` 的客户端。

事件类型包括：

- `sources`
- `token`
- `done`

## 健康检查与可观测性

服务提供以下非业务接口：

- `GET /health`
- `GET /health/ready`
- `GET /metrics`

其中：

- `/health` 用于进程存活检查
- `/health/ready` 用于数据库与 Redis 就绪检查
- `/metrics` 用于输出轻量级 HTTP、retrieval、chat 统计

## 标准化错误返回

业务异常和参数校验异常会统一返回以下结构：

```json
{
  "detail": "Input should be greater than or equal to 32",
  "error_code": "validation_error",
  "retryable": false,
  "request_id": "chat-invalid"
}
```

字段语义如下：

- `detail`
  - 人类可读错误描述
- `error_code`
  - 稳定错误类型，适合上层系统判断
- `retryable`
  - 是否建议调用方重试
- `request_id`
  - 对应本次请求的链路 ID

## 调用建议

如果你是上层平台或前端集成方，推荐优先接入：

- `POST /api/v1/retrieval/search`
- `POST /api/v1/chat/query`

如果你需要更细粒度的实时输出，再单独使用：

- `POST /api/v1/chat/stream`

## 参考文档

- 架构说明：`architecture.md`
- 配置说明：`configuration.md`
- Dify 集成：`integrations/dify.md`
- Docker 部署：`deployment/docker.md`
