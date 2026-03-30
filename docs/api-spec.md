# API 规格

## 基础信息

- Base URL: `http://localhost:8000`
- Prefix: `/api/v1`

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

当依赖未就绪时，接口返回 `503`。

## 1. 上传文档

- Method: `POST`
- Path: `/api/v1/documents/upload`
- Content-Type: `multipart/form-data`

### 表单字段

- `file`: 文档文件

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
  "top_k": 3
}
```

## 5. 同步问答

- Method: `POST`
- Path: `/api/v1/chat/query`

### 请求体

```json
{
  "query": "Summarize the uploaded file.",
  "top_k": 3,
  "system_prompt": "请用中文回答"
}
```

## 6. 流式问答

- Method: `POST`
- Path: `/api/v1/chat/stream`
- Response: `text/event-stream`

### 事件

- `sources`: 返回命中的来源片段
- `token`: 逐步返回回答 token
- `done`: 流结束
