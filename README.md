# Dify FastAPI RAG Tool Service

`Dify FastAPI RAG Tool Service` 是一个面向 `AI 后端` 场景的独立服务，目标是把 `文档上传`、`异步索引`、`向量检索`、`流式问答` 这些核心能力通过 `FastAPI` 暴露出来，并且能作为 `Dify Workflow / Tool` 的外部能力接入。

## 功能

- 文档上传：`POST /api/v1/documents/upload`
- 异步索引：`POST /api/v1/documents/index`
- 任务状态：`GET /api/v1/tasks/{task_id}`
- 检索接口：`POST /api/v1/retrieval/search`
- 同步问答：`POST /api/v1/chat/query`
- 流式问答：`POST /api/v1/chat/stream`

## 技术栈

- `FastAPI`
- `PostgreSQL + pgvector`
- `Redis`
- `Celery`
- `SQLAlchemy`
- `OpenAI-compatible API`
- `Docker Compose`

## 项目结构

```text
app/
  api/
  core/
  models/
  schemas/
  services/
  tasks/
docs/
tests/
```

## 快速启动

1. 复制环境变量：

```bash
cp .env.example .env
```

2. 启动依赖服务与应用：

```bash
docker compose up --build
```

3. 访问：

- OpenAPI: `http://localhost:8000/docs`
- 健康检查: `http://localhost:8000/health`

## 阶段记录

- Week 1：`docs/week1-summary.md`
- Week 2：`docs/week2-summary.md`
- Dify Week 2 复盘：`docs/dify-week2-review.md`

## 环境变量

最少需要配置：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `CHAT_MODEL`
- `EMBEDDING_MODEL`

如果你使用本地或代理模型，只要兼容 OpenAI 的 `chat/completions` 与 `embeddings` 接口即可。

## Dify 集成

建议把此服务配置为 Dify 中的 HTTP 工具：

- 检索场景：调用 `POST /api/v1/retrieval/search`
- 问答场景：调用 `POST /api/v1/chat/query`
- 流式场景：调用 `POST /api/v1/chat/stream`

具体接法见 [docs/dify-integration.md](docs/dify-integration.md)。
也可以直接参考 `integrations/dify-tool.openapi.yaml` 导入工具描述。

## 开发说明

本项目为了压缩 `4~6 周` 路线的交付时间，优先完成了：

- 最小可用 RAG 主链路
- 可独立部署的后端架构
- 与 Dify 集成所需的 HTTP 能力

第一版刻意没有加入：

- 多租户
- 复杂鉴权
- reranker
- 高级评测与可观测性

这些内容可以在后续增强阶段补齐。
