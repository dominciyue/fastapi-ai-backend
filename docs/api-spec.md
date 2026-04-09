# API 规格

## 基础信息

- Base URL: `http://localhost:8000`
- Prefix: `/api/v1`
- 通用响应头：
  - `x-request-id`：本次请求链路 ID
  - `x-response-time-ms`：服务端处理耗时

## 健康检查

### Liveness

- Method: `GET`
- Path: `/health`

返回：

```json
{
  "status": "ok"
}
```

### Readiness

- Method: `GET`
- Path: `/health/ready`

返回示例：

```json
{
  "status": "ok",
  "checks": {
    "database": true,
    "redis": true
  }
}
```

当依赖未就绪时，接口返回 `503`：

```json
{
  "status": "degraded",
  "checks": {
    "database": false,
    "redis": true
  }
}
```

### Metrics

- Method: `GET`
- Path: `/metrics`

返回示例：

```json
{
  "http": {
    "total_requests": 12,
    "total_errors": 1,
    "average_latency_ms": 375.25,
    "requests_by_path": {
      "/api/v1/retrieval/search": 3
    },
    "requests_by_status": {
      "200": 11,
      "422": 1
    }
  },
  "retrieval": {
    "cache_hits": 3,
    "cache_misses": 3,
    "rerank_requests": 5
  },
  "chat": {
    "total_requests": 3,
    "streamed_requests": 1,
    "total_prompt_tokens_estimate": 249,
    "total_completion_tokens_estimate": 24,
    "total_token_estimate": 273,
    "average_context_characters": 378.33,
    "context_truncations": 1
  }
}
```

## 统一错误返回

业务错误和参数校验错误会统一返回以下结构：

```json
{
  "detail": "Input should be greater than or equal to 32",
  "error_code": "validation_error",
  "retryable": false,
  "request_id": "chat-invalid"
}
```

字段说明：

- `detail`：错误描述
- `error_code`：稳定错误类型
- `retryable`：调用方是否适合重试
- `request_id`：可用于日志排查的链路 ID

## 1. 上传文档

- Method: `POST`
- Path: `/api/v1/documents/upload`
- Content-Type: `multipart/form-data`

### 表单字段

- `file`：文档文件

### 返回

```json
{
  "document": {
    "id": "uuid",
    "filename": "sample.md",
    "content_type": "text/markdown",
    "status": "uploaded",
    "chunk_count": 0,
    "created_at": "2026-03-23T07:00:00Z"
  },
  "message": "Document uploaded successfully."
}
```

## 2. 创建索引任务

- Method: `POST`
- Path: `/api/v1/documents/index`
- Content-Type: `application/json`

### 请求体

```json
{
  "document_id": "uuid",
  "metadata": {}
}
```

## 3. 查询任务状态

- Method: `GET`
- Path: `/api/v1/tasks/{task_id}`

## 4. 检索

- Method: `POST`
- Path: `/api/v1/retrieval/search`

### 请求体

```json
{
  "query": "What capabilities does this service support?",
  "top_k": 3,
  "rerank": true
}
```

字段说明：

- `query`：检索问题
- `top_k`：期望返回的命中数，范围 `1~20`
- `rerank`：是否启用轻量关键词重排；不传时使用服务默认配置

### 返回

```json
{
  "query": "What capabilities does this service support?",
  "hits": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "filename": "sample.md",
      "content": "FastAPI service supports upload, indexing, retrieval, and streaming chat.",
      "score": 0.4084,
      "metadata": {
        "source": "sample.md",
        "chunk_index": 0
      }
    }
  ],
  "meta": {
    "request_id": "retrieval-req-1",
    "latency_ms": 228,
    "cache_hit": false,
    "reranked": true,
    "candidate_count": 3,
    "warnings": []
  }
}
```

`meta.warnings` 可能包含：

- `No retrieval hits matched the current query.`
- `Retrieval returned fewer hits than requested.`

## 5. 同步问答

- Method: `POST`
- Path: `/api/v1/chat/query`

### 请求体

```json
{
  "query": "Summarize the uploaded file.",
  "top_k": 3,
  "system_prompt": "请用中文回答",
  "rerank": true,
  "max_context_characters": 3000,
  "max_answer_tokens": 300
}
```

字段说明：

- `query`：用户问题
- `top_k`：参与上下文拼接的检索片段数量
- `system_prompt`：额外系统提示词
- `rerank`：是否启用轻量关键词重排
- `max_context_characters`：上下文字符上限，范围 `200~12000`
- `max_answer_tokens`：下游模型最大输出 token 上限，范围 `32~2048`

### 返回

```json
{
  "answer": "根据提供的上下文，上传的文件描述了 FastAPI 服务支持上传、索引、检索和流式聊天功能。",
  "sources": [
    {
      "filename": "sample.md",
      "content": "FastAPI service supports upload, indexing, retrieval, and streaming chat.",
      "score": 0.4084
    }
  ],
  "meta": {
    "request_id": "chat-req-1",
    "latency_ms": 1616,
    "retrieval_cache_hit": true,
    "retrieval_reranked": true,
    "retrieval_candidate_count": 3,
    "context_characters": 466,
    "context_truncated": false,
    "answer_max_tokens": 300,
    "warnings": [],
    "token_usage": {
      "prompt_tokens_estimate": 96,
      "completion_tokens_estimate": 18,
      "total_tokens_estimate": 114
    }
  }
}
```

`meta.warnings` 可能包含：

- `Retrieval returned fewer hits than requested.`
- `Context was truncated to fit the configured character limit.`
- `Answer was generated without retrieval hits.`

## 6. 流式问答

- Method: `POST`
- Path: `/api/v1/chat/stream`
- Content-Type: `application/json`
- Response: `text/event-stream`

请求体与 `POST /api/v1/chat/query` 相同，支持：

- `query`
- `top_k`
- `system_prompt`
- `rerank`
- `max_context_characters`
- `max_answer_tokens`

### 事件

- `sources`：返回命中的来源片段
- `token`：逐步返回回答 token
- `done`：流结束

### 返回示例

```text
event: sources
data: [{"filename":"sample.md","content":"...","score":0.4084}]

event: token
data: Based

event: token
data: on

event: done
data: [DONE]
```
