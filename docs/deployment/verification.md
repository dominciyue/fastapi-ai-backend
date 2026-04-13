# 验证流程

## 验证目标

部署完成后，建议用统一流程验证以下能力是否可用：

- 服务进程是否存活
- 数据库与 Redis 是否就绪
- 文档上传与异步索引是否正常
- 检索、同步问答和流式问答是否正常
- metrics 是否可访问

## 第一步：健康检查

### Liveness

```bash
curl http://127.0.0.1:8000/health
```

预期返回：

```json
{"status":"ok"}
```

### Readiness

```bash
curl http://127.0.0.1:8000/health/ready
```

预期返回：

```json
{"status":"ok","checks":{"database":true,"redis":true}}
```

## 第二步：一键冒烟验证

最推荐的方式是直接执行：

```bash
python scripts/smoke_all.py
```

这条脚本会串行验证：

1. `GET /health/ready`
2. `POST /api/v1/documents/upload`
3. `POST /api/v1/documents/index`
4. `GET /api/v1/tasks/{task_id}`
5. `POST /api/v1/retrieval/search`
6. `POST /api/v1/chat/query`
7. `POST /api/v1/chat/stream`

## 第三步：分阶段验证

如果你需要定位具体问题，可以按步骤拆开执行：

```bash
python scripts/smoke_upload.py
python scripts/smoke_index.py <document_id>
python scripts/smoke_task.py <task_id>
python scripts/smoke_retrieval.py
python scripts/smoke_query.py
python scripts/smoke_stream.py
```

## 第四步：检查 metrics

```bash
curl http://127.0.0.1:8000/metrics
```

建议关注：

- `http.total_requests`
- `http.total_errors`
- `retrieval.cache_hits`
- `retrieval.cache_misses`
- `retrieval.rerank_requests`
- `chat.total_requests`
- `chat.streamed_requests`
- `chat.context_truncations`

## 第五步：验证调用元信息

建议抽样检查一次业务接口返回，确认以下字段存在：

- 响应头：
  - `x-request-id`
  - `x-response-time-ms`
- 检索响应：
  - `meta.cache_hit`
  - `meta.reranked`
  - `meta.candidate_count`
  - `meta.warnings`
- 问答响应：
  - `meta.context_characters`
  - `meta.context_truncated`
  - `meta.answer_max_tokens`
  - `meta.token_usage`
  - `meta.warnings`

## 建议的验收标准

可以将服务视为“已基本可交付”的最低标准如下：

- `/health` 返回 `200`
- `/health/ready` 返回 `200`
- 一轮 `smoke_all.py` 全部通过
- 同步问答能返回答案与来源
- 流式问答能返回 `sources`、`token`、`done`
- `/metrics` 可访问
- 没有出现持续性的索引失败或维度错误

## 相关文档

- Docker 部署：`docker.md`
- 故障排查：`troubleshooting.md`
- API 说明：`../api.md`
