# Dify 集成

## 集成目标

本服务的推荐角色不是替代 `Dify`，而是作为 `Dify` 的下游能力服务，承接：

- 文档检索
- 同步问答
- 独立 RAG 后端能力输出

推荐分工如下：

- `Dify`
  - 负责工作流编排、上层应用逻辑、结果展示
- 本服务
  - 负责文档索引、向量检索、RAG 问答和流式输出

## 推荐接法

### 方案 A：HTTP Tool

适合：

- 检索工具
- 问答工具
- 外部知识库查询

推荐导入接口：

- `POST /api/v1/retrieval/search`
- `POST /api/v1/chat/query`

推荐导入资产：

- `integrations/dify-tool.openapi.yaml`

### 方案 B：Workflow HTTP Request Node

适合：

- 在 Dify Workflow 中编排检索、回答和后处理
- 让 Dify 负责流程控制，本服务负责底层 RAG 能力

推荐链路：

1. HTTP 请求节点调用 `POST /api/v1/retrieval/search`
2. HTTP 请求节点调用 `POST /api/v1/chat/query`
3. 将 `answer` 作为最终输出，将 `sources` 作为引用信息

## 关于流式接口的边界

本服务提供：

- `POST /api/v1/chat/stream`

它返回 `SSE` 事件流，适合：

- 原生前端页面
- 自定义脚本客户端
- 逐 token 消费响应的自定义调用方

但在当前推荐架构下，不建议把它作为 Dify 外部 HTTP Tool 或 Workflow HTTP Request Node 的主路径，原因是：

- Dify 当前更适合同步请求-响应模式
- 外部上游 `SSE` 作为主集成路径会增加联调复杂度

因此建议：

- `Dify` 接同步检索和同步问答
- 原生客户端单独接流式接口

## 地址配置建议

### 本机浏览器或脚本

- `http://127.0.0.1:8000`

### Dify 容器访问宿主机

- `http://host.docker.internal:8000`

当前 OpenAPI 导入资产默认已包含这两类地址，其中更偏向容器场景的是：

- `http://host.docker.internal:8000`

## 最小导入建议

建议先只导入两项能力：

1. `retrievalSearch`
2. `chatQuery`

这样可以最低成本验证：

- Dify Tool 导入是否成功
- 服务地址是否可达
- 检索与问答链路是否真正跑通

## Workflow 资产

仓库还提供最小工作流资产：

- `integrations/dify-rag-workflow.yml`

它适合用于快速验证：

- Dify Workflow
- 外部 API Tool
- FastAPI RAG 服务

是否已经形成一条可运行的最小联调链路。

## 联调前检查清单

开始接入 Dify 之前，建议先确认：

1. `http://127.0.0.1:8000/health` 返回 `200`
2. `http://127.0.0.1:8000/health/ready` 返回 `200`
3. 已上传并索引过至少一份文档
4. `python scripts/smoke_retrieval.py` 可以拿到结果
5. `python scripts/smoke_query.py` 可以拿到最终回答

## 集成价值

采用这种分层方式的价值在于：

- 将底层知识库能力从平台层中独立出来
- 让 `Dify` 更专注于工作流编排
- 让本服务继续作为独立后端能力对外复用
- 更方便在面试或演示中讲清平台和服务的边界
