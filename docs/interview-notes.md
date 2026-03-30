# 面试讲解提纲

## 一句话介绍

我做了一个可被 `Dify` 调用的 `FastAPI RAG Tool Service`，它把文档上传、异步索引、检索和流式问答能力独立成一个 AI 后端服务。

## 你可以重点讲的点

### 1. 为什么这样设计

- `Dify` 适合做 workflow 编排
- 独立 FastAPI 服务适合承载后端能力与工程化控制
- 两者结合后，平台与服务职责边界更清晰

### 2. 核心链路

- 文件上传
- 后台异步索引
- pgvector 检索
- OpenAI-compatible 模型回答
- SSE 流式输出

### 3. 技术选型

- `FastAPI`：接口开发与 OpenAPI 能力
- `PostgreSQL + pgvector`：减少额外向量数据库部署成本
- `Redis + Celery`：实现异步索引任务
- `OpenAI-compatible API`：兼容多种模型服务

### 4. 工程价值

- 不是单纯调模型 API
- 具备任务状态管理、存储、检索、流式输出和部署能力
- 可以直接接入 `Dify Workflow`

### 5. Week 5 可以重点补充的可信度

- 增加 `GitHub Actions CI`，把 `ruff check .` 和 `pytest` 固化成持续校验
- 补充演示 / 交付态的 `docker-compose.prod.yml`，关闭热重载并增加重启策略
- 整理正式部署说明，降低本地联调和现场演示的不确定性

## 适合直接讲给面试官的两分钟版本

我没有把这个项目做成一个只会调模型 API 的 demo，而是拆成了一个可独立部署的 `FastAPI RAG` 服务，再把它接到 `Dify` 里做 workflow 编排。这样我既能展示后端工程能力，比如异步任务、向量检索、流式输出、部署与健康检查，也能展示我对 AI 应用平台边界的理解。

这套服务里，文档上传后会进入异步索引流程，文本被切块、生成 embedding，落到 `PostgreSQL + pgvector` 里；检索和同步问答接口适合直接给 `Dify Tool` 调用，流式问答则保留给原生客户端消费 `SSE`。我还特意把 chat 和 embedding 提供方拆开配置，这样可以用 `DeepSeek` 做聊天、用 `DashScope` 做 embedding，更符合国内可用性的实际情况。

在工程化上，我补了 smoke scripts、CI、部署文档和演示态 compose 配置，所以这个项目不仅能本地跑通，也更适合录屏演示、现场答辩和后续继续增强。

## 可继续加强的方向

- reranker
- 缓存
- tracing / metrics
- 权限与多租户
- 更严格的测试与迁移体系
