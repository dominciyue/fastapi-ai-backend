# Dify 集成说明

## 集成目标

把本服务作为 `Dify` 的外部 HTTP Tool 或 Workflow 节点调用目标。

## 推荐接法

### 方案 A：HTTP Tool

适合：

- 检索工具
- 问答工具
- 外部知识库查询

推荐映射：

- `POST /api/v1/retrieval/search`
- `POST /api/v1/chat/query`

导入方式：

- 直接使用 `integrations/dify-tool.openapi.yaml`
- 在 `Dify` 中导入为外部工具
- 不需要额外鉴权时，可先按无认证方式联调

推荐原因：

- `Dify` 更擅长编排工具调用和上层应用
- 当前服务更适合承接底层 `RAG` 检索与回答能力
- 这条路径最容易形成可演示、可面试讲述的“平台 + 服务”边界

### 方案 B：Workflow HTTP Request Node

适合：

- 在 Dify Workflow 中编排检索、回答、后处理
- 让 Dify 负责上层流程，本服务负责底层 RAG 能力

推荐映射：

- 检索阶段：`POST /api/v1/retrieval/search`
- 最终回答阶段：`POST /api/v1/chat/query`

## 关于流式接口的边界

当前服务已经提供：

- `POST /api/v1/chat/stream`

它返回的是 `SSE` 事件流，适合：

- 原生前端页面
- 自己写的脚本客户端
- 需要逐 token 消费响应的自定义调用方

但在当前阶段，不建议把它作为 `Dify` 的外部 HTTP Tool / Workflow HTTP Request Node 直接接入，原因是：

- `Dify` 现有 HTTP Tool / HTTP Request Node 更适合同步请求-响应模式
- 外部上游 `SSE` 流式返回不适合作为当前这条集成链路的主路径

因此 Week 4 的集成策略是：

- `Dify`：先接同步检索和同步问答
- `FastAPI`：继续保留原生 `SSE` 接口，供独立客户端直接调用

## 地址配置建议

如果 `Dify` 和 `FastAPI` 都跑在本机开发环境，常用地址如下：

- 浏览器/本机脚本访问：`http://127.0.0.1:8000`
- `Dify` 容器内访问宿主机服务：`http://host.docker.internal:8000`

当前仓库里的 `integrations/dify-tool.openapi.yaml` 默认使用：

- `http://host.docker.internal:8000`

这样更适合把 `Dify` 跑在容器里、本服务跑在宿主机或另一套本地开发容器里。

## 导入建议

推荐先在 `Dify` 中导入两个能力：

1. `retrievalSearch`
2. `chatQuery`

对应能力分别是：

- 文档片段检索
- 带引用来源的同步回答

## 示例请求

## 示例请求

### 检索

```json
{
  "query": "如何部署这个服务？",
  "top_k": 5
}
```

### 问答

```json
{
  "query": "这个项目的核心能力是什么？",
  "top_k": 5,
  "system_prompt": "请用中文给出简洁回答。"
}
```

## Workflow 编排建议

如果要在 `Dify Workflow` 中做最小联调，建议先采用这条最稳路径：

1. 用户问题输入
2. HTTP 请求节点调用 `POST /api/v1/retrieval/search`
3. 把检索结果作为上下文展示或传给后续节点
4. HTTP 请求节点调用 `POST /api/v1/chat/query`
5. 将 `answer` 作为最终输出，将 `sources` 作为引用信息展示

这样做的优点是：

- 联调最简单
- 失败点最少
- 最容易验证“Dify 编排 + 外部 RAG 服务”是否已经真正打通

## 联调前最小检查清单

开始接 `Dify` 之前，先确认：

1. `FastAPI` 服务在 `http://127.0.0.1:8000/health` 返回 `200`
2. 已上传并索引过至少一份文档
3. `python scripts/smoke_retrieval.py` 能拿到结果
4. `python scripts/smoke_query.py` 能拿到最终回答
5. 如果需要直接验证流式能力，再额外执行 `python scripts/smoke_stream.py`

## 在 Dify 中的价值

- 将文档索引与检索能力从应用平台中拆出来
- 使 `Dify` 更适合编排，而本服务专注 AI 后端能力
- 面试时可以完整讲清楚平台与服务的边界
