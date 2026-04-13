# Dify FastAPI RAG Tool Service

`Dify FastAPI RAG Tool Service` 是一个面向 AI Backend 场景的独立 RAG 后端服务，用于把文档上传、异步索引、向量检索、同步问答和流式问答能力以标准 HTTP 接口暴露出来，并作为 `Dify` 或其他上层系统的下游能力层接入。

## 项目价值

这个项目重点展示的是一条可交付、可部署、可集成、可观测的 AI 后端能力链路，而不是完整 SaaS 平台。

它适合用于：

- 独立封装知识库检索与问答能力
- 对接 `Dify Workflow` / HTTP Tool
- 本地演示、联调和交付验证
- 作为 AI 后端面试作品展示架构、异步任务、缓存和接口设计能力

## 核心能力

- 文档上传：`POST /api/v1/documents/upload`
- 异步索引：`POST /api/v1/documents/index`
- 任务状态查询：`GET /api/v1/tasks/{task_id}`
- 检索接口：`POST /api/v1/retrieval/search`
- 同步问答：`POST /api/v1/chat/query`
- 流式问答：`POST /api/v1/chat/stream`
- 健康检查：`GET /health`
- 就绪检查：`GET /health/ready`
- 轻量 metrics：`GET /metrics`
- Redis 检索缓存
- 轻量关键词 rerank
- 请求级 `x-request-id`
- 响应耗时头 `x-response-time-ms`
- 标准化错误结构与调用方 warnings

## 技术栈

- `FastAPI`
- `PostgreSQL + pgvector`
- `Redis`
- `Celery`
- `SQLAlchemy`
- `OpenAI-compatible API`
- `Docker Compose`
- `GitHub Actions CI`

## 快速启动

1. 复制配置文件：

```bash
cp .env.example .env
```

2. 启动服务：

```bash
docker compose up --build
```

如果你需要更稳定的演示 / 交付环境，建议使用：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

3. 访问：

- OpenAPI：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`
- 就绪检查：`http://localhost:8000/health/ready`

## 最小验证

服务启动后，推荐直接运行：

```bash
python scripts/smoke_all.py
```

这会串行验证上传、索引、检索、同步问答和流式问答的完整主链路。

## 文档导航

- 项目概览：`docs/overview.md`
- 架构设计：`docs/architecture.md`
- API 说明：`docs/api.md`
- 配置说明：`docs/configuration.md`
- Docker 部署：`docs/deployment/docker.md`
- 验证流程：`docs/deployment/verification.md`
- 故障排查：`docs/deployment/troubleshooting.md`
- 可观测性：`docs/operations/observability.md`
- Dify 集成：`docs/integrations/dify.md`
- 数据模型：`docs/reference/database.md`

## 配置说明

最少需要确认以下配置：

- `DATABASE_URL`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `CHAT_MODEL`
- `EMBEDDING_MODEL`

如果 chat 与 embedding 不在同一个提供方，还可以拆开配置：

- `CHAT_BASE_URL`
- `CHAT_API_KEY`
- `EMBEDDING_BASE_URL`
- `EMBEDDING_API_KEY`
- `EMBEDDING_DIMENSION`

详细说明见 `docs/configuration.md`。

## Dify 集成

推荐把本服务作为 Dify 的外部能力层接入：

- 优先导入：
  - `POST /api/v1/retrieval/search`
  - `POST /api/v1/chat/query`
- `POST /api/v1/chat/stream` 更适合原生客户端直接消费，不作为当前推荐的 Dify 主路径

可直接使用：

- `integrations/dify-tool.openapi.yaml`
- `integrations/dify-rag-workflow.yml`

详细说明见 `docs/integrations/dify.md`。

## 工程化能力

当前项目已经具备以下工程化基础：

- `GitHub Actions CI`
- Docker 开发态与稳定演示态双 compose 方案
- `health` / `readiness` 检查
- 轻量 `/metrics`
- 检索缓存与 rerank
- 请求级追踪与响应耗时
- 容器环境下的一键冒烟验证

## 当前边界

当前版本刻意不覆盖以下范围：

- 多租户
- 复杂鉴权
- 独立 reranker 模型服务
- 完整 tracing / APM 平台
- 企业级权限体系

因此它更适合作为独立 RAG 后端服务样本，而不是完整业务平台。
