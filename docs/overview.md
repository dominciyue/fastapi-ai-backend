# 项目概览

## 项目定位

`Dify FastAPI RAG Tool Service` 是一个面向 AI 后端场景的独立服务，用于把文档上传、异步索引、向量检索、同步问答和流式问答能力以标准 HTTP 接口形式暴露出来。

这个项目的核心价值不在于提供完整的应用平台，而在于提供一个：

- 可独立部署的 RAG 后端服务
- 可被 `Dify` 等上层平台接入的外部能力层
- 适合演示、交付、联调和面试讲解的工程样本

## 适用场景

当前项目适合以下场景：

- 将文档知识库能力独立封装成后端服务
- 作为 `Dify Workflow` 或外部 HTTP Tool 的下游能力提供方
- 本地或演示环境中快速验证 RAG 主链路
- 作为 AI Backend 面试作品展示架构、接口设计、异步任务、缓存和可观测性能力

## 当前能力范围

服务当前已经提供：

- 文档上传与本地存储
- 异步索引任务投递与状态跟踪
- 基于 `pgvector` 的向量检索
- 基于关键词重叠的轻量 rerank
- Redis 检索缓存
- 同步问答与 `SSE` 流式问答
- 请求级 `request_id`
- 健康检查、就绪检查与轻量 metrics
- 面向调用方的标准化错误结构和 warnings

## 非目标范围

为了保持项目边界清晰，当前版本刻意不覆盖以下能力：

- 多租户隔离
- 复杂鉴权体系
- 完整的后台管理界面
- 专业级 tracing / APM 平台接入
- 独立 reranker 模型服务
- 企业级权限模型与审计能力

这意味着它更适合作为“可交付、可扩展的后端能力样本”，而不是一个完整 SaaS 产品。

## 公开文档导航

- 架构设计：`architecture.md`
- API 说明：`api.md`
- 配置说明：`configuration.md`
- Docker 部署：`deployment/docker.md`
- 验证流程：`deployment/verification.md`
- 故障排查：`deployment/troubleshooting.md`
- 可观测性：`operations/observability.md`
- Dify 集成：`integrations/dify.md`
- 数据模型：`reference/database.md`

## 适合如何理解这个项目

如果从工程角色来理解，可以把这个项目看成三层：

1. `FastAPI` 暴露统一接口，承接外部调用
2. `Celery + Redis` 负责异步索引任务
3. `PostgreSQL + pgvector` 负责向量存储与检索

而 `Dify` 在推荐架构里属于上层编排平台，不直接承担底层索引和检索实现。
