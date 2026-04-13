# 配置说明

## 配置目标

本项目通过环境变量控制数据库、缓存、异步任务和模型接入行为。配置设计重点是：

- 支持 chat 与 embedding 提供方拆分
- 支持 embedding 维度显式校验
- 支持检索缓存、rerank 和回答约束的运行时开关

建议从 `.env.example` 复制出本地 `.env` 后再按需修改。

## 基础运行配置

基础服务相关变量包括：

- `APP_NAME`
- `APP_ENV`
- `APP_HOST`
- `APP_PORT`
- `APP_DEBUG`
- `API_PREFIX`
- `LOG_LEVEL`

## 存储与队列配置

### PostgreSQL

- `DATABASE_URL`

用于保存文档、索引任务和向量分片。

### Redis

- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

Redis 同时承担：

- Celery broker
- Celery result backend
- 检索缓存存储

## 模型配置

### 通用兼容模式

- `OPENAI_BASE_URL`
- `OPENAI_API_KEY`

当 chat 与 embedding 共用同一上游时，可直接使用这组变量。

### 拆分 chat 与 embedding 提供方

如果聊天模型和 embedding 模型不在同一个提供方，可以分别配置：

- `CHAT_BASE_URL`
- `CHAT_API_KEY`
- `CHAT_MODEL`
- `EMBEDDING_BASE_URL`
- `EMBEDDING_API_KEY`
- `EMBEDDING_MODEL`
- `EMBEDDING_DIMENSION`

这种方式适合：

- `DeepSeek` 做 chat
- `DashScope` 或其他兼容 OpenAI embeddings 的服务做向量化

## 向量维度约束

`EMBEDDING_DIMENSION` 必须与实际 embedding 服务返回的向量维度一致。

这是因为：

- `pgvector` 列维度在表结构层固定
- 维度不一致会导致索引链路失败

如果你切换了 embedding 提供方，例如从 `1536` 切到 `1024`，通常需要：

1. 重建本地数据库卷或迁移表结构
2. 重新上传文档
3. 重新执行索引

建议在正式索引前先运行：

```bash
python scripts/check_embedding_provider.py
```

## 检索与回答行为配置

### 检索默认行为

- `RETRIEVAL_TOP_K`
- `ENABLE_RETRIEVAL_CACHE`
- `RETRIEVAL_CACHE_TTL_SECONDS`
- `ENABLE_KEYWORD_RERANK`
- `RERANK_CANDIDATE_MULTIPLIER`

这些配置决定：

- 默认召回数量
- 是否启用 Redis 检索缓存
- 缓存有效期
- 是否启用轻量关键词 rerank
- rerank 前候选召回的放大倍数

### 上下文与回答约束

- `MAX_CONTEXT_CHARACTERS`
- `MAX_ANSWER_TOKENS`

这些变量用于控制：

- 拼接给模型的上下文长度
- 下游模型允许的最大输出上限

## 文档处理配置

- `CHUNK_SIZE`
- `CHUNK_OVERLAP`
- `MAX_FILE_SIZE_MB`
- `MAX_CONTEXT_CHUNKS`
- `STORAGE_DIR`
- `UPLOAD_DIR`

这些配置影响：

- 文档切片策略
- 单文件大小限制
- 本地存储路径
- 问答上下文允许使用的最大片段数

## 配置建议

### 本地开发

推荐：

- 使用 `docker-compose.yml`
- 保持 `APP_DEBUG=true`
- 优先确认数据库、Redis、模型配置可达

### 稳定演示或交付

推荐：

- 使用 `docker-compose.yml + docker-compose.prod.yml`
- 明确固定 chat / embedding 模型配置
- 提前验证 `/health/ready` 和 `scripts/smoke_all.py`

## 安全注意事项

- 不要把真实 API Key 提交到仓库
- 不要把本地 `.env` 推送到远端
- 生产环境应使用外部密钥管理方式，而不是将密钥写死在镜像中

## 参考文档

- API 说明：`api.md`
- Docker 部署：`deployment/docker.md`
- 故障排查：`deployment/troubleshooting.md`
