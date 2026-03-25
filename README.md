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
- Week 3：`docs/week3-summary.md`
- Dify Week 2 复盘：`docs/dify-week2-review.md`

## 环境变量

最少需要配置：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `CHAT_MODEL`
- `EMBEDDING_MODEL`

如果你使用本地或代理模型，只要兼容 OpenAI 的 `chat/completions` 与 `embeddings` 接口即可。

如果你的聊天模型和 embedding 模型不在同一个提供方，也可以拆开配置：

- `CHAT_BASE_URL`
- `CHAT_API_KEY`
- `EMBEDDING_BASE_URL`
- `EMBEDDING_API_KEY`

例如使用 `DeepSeek` 做聊天时，可以只配置：

- `CHAT_BASE_URL=https://api.deepseek.com/v1`
- `CHAT_API_KEY=<your-key>`
- `CHAT_MODEL=deepseek-chat`

如果暂时没有独立的 embedding 服务，项目会继续使用本地 mock embedding 作为演示模式，不会阻塞主链路联调。

## 真实 Embedding 接入

当前项目已经支持把 `chat` 和 `embedding` 拆开配置，但需要注意：

- 你现在使用的 `DeepSeek` 账号只暴露了 `deepseek-chat` 和 `deepseek-reasoner`
- 该账号下未发现可用的 embedding 模型
- 直接请求 `https://api.deepseek.com/v1/embeddings` 会返回 `404`

这意味着：

- `DeepSeek` 目前适合继续做聊天模型
- 真实 embedding 需要接入另一个兼容 OpenAI `/embeddings` 的提供方

你需要额外准备：

- `EMBEDDING_BASE_URL`
- `EMBEDDING_API_KEY`
- `EMBEDDING_MODEL`
- `EMBEDDING_DIMENSION`

配置完成后，可先运行：

```bash
python scripts/check_embedding_provider.py
```

它会输出：

- 当前 embedding 服务地址
- 当前 embedding 模型名
- 配置的维度
- 实际返回的向量维度

如果返回维度和 `EMBEDDING_DIMENSION` 不一致，项目现在会直接报清晰错误，避免你在索引中途才发现问题。

### 维度切换提醒

`pgvector` 列维度是在表结构里固定的。

如果你从 mock / 旧 embedding 模型切到新的真实 embedding 模型，且维度发生变化，例如：

- `1536 -> 1024`

那么你需要在本地重新创建或迁移数据库结构后，再重新做索引。对于当前演示项目，最直接的方式通常是重建本地容器数据卷后重新上传并索引文档。

## Dify 集成

建议把此服务配置为 Dify 中的 HTTP 工具或 Workflow 的 HTTP 请求节点：

- `Dify` 工具接入优先使用：
  - `POST /api/v1/retrieval/search`
  - `POST /api/v1/chat/query`
- `POST /api/v1/chat/stream` 保留给原生前端、脚本或自定义客户端直接消费 `SSE`
- 当前 `Dify` 不适合直接把外部 `SSE` 上游流作为 HTTP Tool / HTTP Request Node 的输入

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

## 冒烟测试

服务启动后，可以按下面顺序做一轮最小链路验证：

```bash
python scripts/smoke_upload.py
python scripts/smoke_index.py <document_id>
python scripts/smoke_task.py <task_id>
python scripts/smoke_retrieval.py
python scripts/smoke_query.py
python scripts/smoke_stream.py
```
