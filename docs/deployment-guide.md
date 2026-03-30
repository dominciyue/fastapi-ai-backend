# 部署指南

这份文档面向 `Week 5` 的工程化阶段，目标是把当前项目从“本地开发可跑”推进到“可稳定演示、可复现交付”的状态。

## 部署目标

当前仓库提供两套运行方式：

- `docker-compose.yml`：偏开发环境，`api` 服务默认带 `--reload`
- `docker-compose.prod.yml`：偏演示 / 交付环境，关闭热重载并补上重启策略与 `readiness` 检查

如果你只是本地开发，继续使用默认 compose 即可。

如果你要做录屏、联调、答辩或面试演示，建议使用生产覆盖文件。

## 前置条件

- 已安装 `Docker Desktop`
- 本机可正常执行 `docker compose`
- 已复制 `.env.example` 为 `.env`

```bash
cp .env.example .env
```

## 关键环境变量

至少确认以下配置已经可用：

- `DATABASE_URL`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `CHAT_MODEL`
- `EMBEDDING_MODEL`

如果聊天模型和 embedding 模型来自不同提供方，再额外配置：

- `CHAT_BASE_URL`
- `CHAT_API_KEY`
- `EMBEDDING_BASE_URL`
- `EMBEDDING_API_KEY`
- `EMBEDDING_DIMENSION`

注意事项：

- 不要把真实 API Key 提交到仓库
- 切换 embedding 供应商时，要确认向量维度是否一致
- 如果从 `1536` 切到 `1024` 之类的新维度，通常需要重建本地数据库卷后重新索引

## 本地演示部署

建议使用下面这条命令启动更稳定的演示环境：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

启动后检查服务状态：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

## 验证步骤

1. 健康检查

```bash
curl http://127.0.0.1:8000/health
```

预期返回：

```json
{"status":"ok"}
```

建议再检查一次依赖是否可用：

```bash
curl http://127.0.0.1:8000/health/ready
```

预期返回：

```json
{"status":"ok","checks":{"database":true,"redis":true}}
```

2. 运行最小冒烟链路

优先推荐一键执行：

```bash
python scripts/smoke_all.py
```

如果你需要逐步定位问题，再拆成单步脚本：

```bash
python scripts/smoke_upload.py
python scripts/smoke_index.py <document_id>
python scripts/smoke_task.py <task_id>
python scripts/smoke_retrieval.py
python scripts/smoke_query.py
python scripts/smoke_stream.py
```

3. 如果需要接入 `Dify`

- 导入 `integrations/dify-tool.openapi.yaml`
- 或直接导入 `integrations/dify-rag-workflow.yml`
- 确认 `Dify` 到服务端的地址可达

本机 Docker 场景下，常见地址如下：

- `http://host.docker.internal:8000`
- `http://127.0.0.1:8000`

## 停止与清理

停止服务：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

如果只是重启服务，不建议随意删除数据卷。

只有在你确认测试数据可丢弃，且需要重建向量维度或数据库状态时，再执行：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v
```

## 常见问题

### 1. `chat` 正常但索引失败

优先检查 embedding 配置是否正确：

```bash
python scripts/check_embedding_provider.py
```

重点看：

- 当前实际调用的是不是你预期的 embedding 服务
- 返回向量维度是否和 `EMBEDDING_DIMENSION` 一致

### 2. `Dify` 调不到 FastAPI 服务

优先检查：

- `FastAPI` 是否真的在 `8000` 端口运行
- `Dify` 容器里是否应该使用 `host.docker.internal`
- Docker Desktop 重启后，FastAPI 这套 compose 是否被重新拉起

### 3. 录屏或演示时接口偶发抖动

建议：

- 使用 `docker-compose.prod.yml`，不要继续跑带 `--reload` 的开发命令
- 先完成一轮上传、索引、检索、问答的预热
- 演示前固定好一份文档和一组问题，避免变量过多

## 面试表达建议

部署部分可以这样讲：

- 这个项目不只是一个本地 demo，我把开发态和演示态的 compose 拆开了
- 演示态关闭热重载，并补了重启策略和依赖级 `readiness` 检查，降低现场联调风险
- 配合 smoke scripts，可以快速证明上传、索引、检索、问答、流式输出整条链路是通的
