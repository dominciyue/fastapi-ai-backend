# 数据库设计

## documents

用途：保存原始上传文档及其索引状态。

字段：

- `id`: 主键 UUID
- `filename`: 原始文件名
- `content_type`: MIME 类型
- `storage_path`: 文件存储路径
- `status`: `uploaded | indexing | indexed | failed`
- `metadata`: 扩展元数据
- `chunk_count`: 已切片数量
- `error_message`: 索引失败原因
- `created_at`
- `updated_at`

## indexing_tasks

用途：记录异步索引任务状态。

字段：

- `id`: 主键 UUID
- `document_id`: 关联 `documents.id`
- `celery_task_id`: Celery 任务 id
- `status`: `queued | started | completed | failed`
- `detail`: 状态说明
- `created_at`
- `updated_at`

## document_chunks

用途：保存切片文本和向量。

字段：

- `id`: 主键 UUID
- `document_id`: 关联 `documents.id`
- `chunk_index`: 文档内分片序号
- `content`: 片段文本
- `metadata`: 片段元数据
- `embedding`: `pgvector` 向量
- `created_at`

## 当前约束与取舍

- 单租户设计
- 不做软删除
- 不引入 Alembic，先由 SQLAlchemy 初始化表
- 向量库优先使用 `pgvector`，降低本地开发复杂度
