# 数据模型

## 目标

当前数据库设计围绕最小可用 RAG 主链路展开，重点覆盖：

- 原始文档管理
- 异步索引任务跟踪
- 文本分片与向量存储

## `documents`

用途：保存原始上传文档及其索引状态。

核心字段：

- `id`
- `filename`
- `content_type`
- `storage_path`
- `status`
- `metadata`
- `chunk_count`
- `error_message`
- `created_at`
- `updated_at`

关注点：

- 文档上传后先进入原始记录层
- 索引结果和错误信息会回写到这张表

## `indexing_tasks`

用途：记录异步索引任务状态。

核心字段：

- `id`
- `document_id`
- `celery_task_id`
- `status`
- `detail`
- `created_at`
- `updated_at`

关注点：

- 用于前端或脚本轮询异步索引进度
- 与 `documents` 解耦，避免上传请求同步阻塞

## `document_chunks`

用途：保存文本分片与向量。

核心字段：

- `id`
- `document_id`
- `chunk_index`
- `content`
- `metadata`
- `embedding`
- `created_at`

关注点：

- `embedding` 使用 `pgvector`
- `chunk_index` 保留文档内顺序
- `metadata` 可用于后续扩展来源信息

## 当前设计取舍

- 单租户设计
- 不做软删除
- 先由 SQLAlchemy 初始化表，不引入 Alembic
- 优先使用 `pgvector`，降低本地开发与演示复杂度

## 向量维度注意事项

向量维度依赖 `EMBEDDING_DIMENSION`，并与 `document_chunks.embedding` 的实际存储结构强相关。

如果你更换 embedding 提供方并导致维度变化，通常需要：

1. 重建本地数据库结构或迁移表
2. 重新上传文档
3. 重新索引

## 与业务链路的关系

- `documents`
  - 回应“上传了什么、当前索引状态如何”
- `indexing_tasks`
  - 回应“异步任务现在进行到哪一步”
- `document_chunks`
  - 回应“问答和检索真正依赖的上下文来自哪里”
