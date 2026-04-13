# 故障排查

## `chat` 正常但索引失败

优先检查 embedding 配置是否正确：

```bash
python scripts/check_embedding_provider.py
```

重点确认：

- 当前实际调用的是不是预期的 embedding 服务
- 实际返回的向量维度是否与 `EMBEDDING_DIMENSION` 一致

如果维度不一致，通常需要：

1. 重建数据库卷或调整表结构
2. 重新上传文档
3. 重新索引

## `Dify` 调不到 FastAPI 服务

优先检查：

- `FastAPI` 是否真的运行在 `8000` 端口
- `Dify` 容器内访问宿主机时是否应使用 `host.docker.internal`
- Docker Desktop 重启后，这套 FastAPI compose 是否重新拉起

如果是容器到宿主机访问，优先尝试：

- `http://host.docker.internal:8000`

## Docker Desktop 重启后接口不可用

常见原因是：

- Docker 引擎重启后 `api` / `worker` / `postgres` / `redis` 没有自动恢复

建议执行：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

然后重新检查：

- `docker compose ps`
- `/health`
- `/health/ready`

## 演示或录屏时接口偶发抖动

建议：

- 使用 `docker-compose.prod.yml`
- 不要继续运行带 `--reload` 的开发模式
- 演示前先做一轮上传、索引、检索、问答预热
- 固定演示文档和问题，降低变量

## 检索结果不稳定或质量一般

优先检查：

- 是否启用了 `ENABLE_KEYWORD_RERANK`
- `RERANK_CANDIDATE_MULTIPLIER` 是否过低
- 上传文档是否过少或切片质量不佳

如果你只是验证工程能力，这类轻量 rerank 已足够。

如果你追求更高质量，可以在后续引入更真实的 reranker 模型服务。

## `/health/ready` 返回失败

优先看：

- `database` 是否为 `true`
- `redis` 是否为 `true`

通常对应问题包括：

- PostgreSQL 未启动
- Redis 未启动
- `.env` 中连接串与容器网络不一致

## 请求返回 `422`

优先检查是否触发了参数校验限制，例如：

- `top_k` 超出范围
- `max_context_characters` 小于最小值
- `max_answer_tokens` 小于最小值

当前服务会返回标准化错误结构，建议关注：

- `error_code`
- `retryable`
- `request_id`

## 相关文档

- 配置说明：`../configuration.md`
- 验证流程：`verification.md`
- Dify 集成：`../integrations/dify.md`
