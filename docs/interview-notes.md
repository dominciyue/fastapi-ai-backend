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

## 可继续加强的方向

- reranker
- 缓存
- tracing / metrics
- 权限与多租户
- 更严格的测试与迁移体系
