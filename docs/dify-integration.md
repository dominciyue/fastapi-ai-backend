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

### 方案 B：Workflow HTTP Request Node

适合：

- 在 Dify Workflow 中编排检索、回答、后处理
- 让 Dify 负责上层流程，本服务负责底层 RAG 能力

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

## 在 Dify 中的价值

- 将文档索引与检索能力从应用平台中拆出来
- 使 `Dify` 更适合编排，而本服务专注 AI 后端能力
- 面试时可以完整讲清楚平台与服务的边界
