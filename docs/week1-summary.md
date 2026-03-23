# Week 1 总结

## 本周目标

完成 `Dify + FastAPI` 双主线的第一阶段冻结：

- 跑通 `Dify` 本地开发底座
- 冻结 `FastAPI` 项目题目与接口范围
- 搭起可运行的 `FastAPI RAG Tool Service` 第一版
- 形成可继续推进的 issue 清单、启动记录和测试方法

## 我们已经完成了什么

### Dify 侧

- 拉取了 `Dify` 仓库到 `E:\Github高星项目\dify`
- 阅读并确认了和本地开发最相关的资料：
  - `README`
  - `CONTRIBUTING`
  - `api/README`
  - `docker` 相关说明
- 跑通了 `Dify` 开发中间件栈：
  - `db_postgres`
  - `redis`
  - `sandbox`
  - `ssrf_proxy`
  - `weaviate`
  - `plugin_daemon`
- 产出了：
  - `docs/dify-local-startup.md`
  - `docs/dify-issues.md`
- 筛出了首个最稳妥的贡献切口：
  - `#33699` `bump pyrefly version`
- 并已经在本地落地了这次 Dify 改动：
  - `dify/api/pyproject.toml` 中 `pyrefly` 从 `>=0.55.0` 升级到 `>=0.57.0`
  - `dify/api/uv.lock` 更新到了 `pyrefly 0.57.1`

### FastAPI 侧

- 创建了项目目录 `E:\Github高星项目\fastapi-ai-backend`
- 完成了第一版项目骨架：
  - `app/api`
  - `app/core`
  - `app/models`
  - `app/schemas`
  - `app/services`
  - `app/tasks`
- 完成了最小功能面：
  - `POST /api/v1/documents/upload`
  - `POST /api/v1/documents/index`
  - `GET /api/v1/tasks/{task_id}`
  - `POST /api/v1/retrieval/search`
  - `POST /api/v1/chat/query`
  - `POST /api/v1/chat/stream`
- 完成了基础工程化文件：
  - `pyproject.toml`
  - `Dockerfile`
  - `docker-compose.yml`
  - `.env.example`
  - `README.md`
- 补充了文档资产：
  - `docs/architecture.md`
  - `docs/dify-integration.md`
  - `docs/api-spec.md`
  - `docs/db-schema.md`
  - `docs/interview-notes.md`
  - `integrations/dify-tool.openapi.yaml`
- 补充了本地验证脚本：
  - `scripts/smoke_upload.py`
  - `scripts/smoke_index.py`
  - `scripts/smoke_task.py`
  - `scripts/smoke_stream.py`
- 补充了测试：
  - `tests/test_chunker.py`
  - `tests/test_document_parser.py`
  - `tests/test_llm_client.py`

## 遇到的问题

### 1. Docker Engine 没启动

现象：

- `docker compose up --build` 无法连接 Docker Desktop Linux Engine

处理：

- 重启机器后恢复正常

### 2. 首次构建时拉基础镜像失败

现象：

- `python:3.11-slim` 在 compose 构建阶段出现 `403 Forbidden`

处理：

- 先单独执行 `docker pull python:3.11-slim`
- 再重新 `docker compose up --build`

### 3. FastAPI 索引链路因缺少模型 API key 失败

现象：

- 文档上传成功
- 索引任务执行时请求 `embeddings` 返回 `401 Unauthorized`

处理：

- 在 `app/services/llm_client.py` 中增加了本地 demo fallback
- 未配置 `OPENAI_API_KEY` 时，仍可完成：
  - mock embedding
  - mock chat
  - mock stream chat

结果：

- 现在本地不依赖真实模型 key，也能演示完整主链路

### 4. Dify 与 FastAPI 的端口冲突

现象：

- `Dify` 中间件默认也要占用 `5432` 和 `6379`
- 与 `fastapi-ai-backend` 的 `Postgres / Redis` 冲突

处理：

- 在 `dify/docker/middleware.env` 中改为：
  - `EXPOSE_POSTGRES_PORT=15432`
  - `EXPOSE_REDIS_PORT=16379`

### 5. Dify compose 变量没有按预期生效

现象：

- 只写 `env_file` 不能让 compose 在解析端口映射时自动读取变量

处理：

- 启动命令必须显式带上：

```bash
docker compose --env-file middleware.env -f docker-compose.middleware.yaml -p dify up -d
```

### 6. plugin daemon 启动初期短暂重启

现象：

- `plugin_daemon` 在数据库还未 ready 时会报连接失败并重启

处理：

- 继续观察
- 等 `db_postgres` 完全 ready 后会自动恢复

结论：

- 这是启动时序问题，不是当前阻塞项

## FastAPI 应该怎么启动

### 方式 A：Docker Compose

执行目录：

- `E:\Github高星项目\fastapi-ai-backend`

启动：

```bash
docker compose up --build -d
```

查看状态：

```bash
docker compose ps
```

访问：

- OpenAPI: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

停止：

```bash
docker compose down
```

### 方式 B：本地 Python 运行

如需本地直接运行，可在项目目录安装依赖后执行：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
celery -A worker.celery_app worker --loglevel=INFO
```

前提：

- 需要自行准备 `Postgres`
- 需要自行准备 `Redis`
- `.env` 配置正确

## FastAPI 应该怎么测试

### 自动化测试

```bash
pytest
ruff check .
```

### 接口冒烟测试

先确保容器已启动，然后执行：

```bash
python scripts/smoke_upload.py
python scripts/smoke_index.py <document_id>
python scripts/smoke_task.py <task_id>
python scripts/smoke_stream.py
```

### 最小人工验证

1. 访问 `http://127.0.0.1:8000/health`
2. 打开 `http://127.0.0.1:8000/docs`
3. 上传测试文件
4. 创建索引任务
5. 查询任务状态是否变为 `completed`
6. 调用检索接口
7. 调用同步问答接口
8. 调用流式问答接口

## Dify 应该怎么启动

执行目录：

- `E:\Github高星项目\dify\docker`

启动：

```bash
docker compose --env-file middleware.env -f docker-compose.middleware.yaml -p dify up -d
```

查看状态：

```bash
docker compose --env-file middleware.env -f docker-compose.middleware.yaml -p dify ps
```

停止：

```bash
docker compose --env-file middleware.env -f docker-compose.middleware.yaml -p dify down
```

当前宿主机映射：

- `Postgres -> 15432`
- `Redis -> 16379`
- `Weaviate -> 8080`
- `Plugin Daemon -> 5002/5003`

## Dify 应该怎么测试

### 中间件存活测试

```bash
docker compose --env-file middleware.env -f docker-compose.middleware.yaml -p dify ps
```

重点确认：

- `db_postgres` healthy
- `redis` healthy
- `sandbox` healthy
- `plugin_daemon` up

### Weaviate 健康检查

```bash
python -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8080/v1/.well-known/ready').status)"
```

期望返回：

- `200`

### Dify API 下一步

当前已跑通的是开发中间件底座。下一步如果要继续完整跑 Dify 后端，需要：

1. 补 `api/.env`
2. 执行 `uv sync --group dev`
3. 数据库迁移
4. 启动 `api`
5. 再连接 `plugin_daemon` 和后续 web

## 当前结论

Week 1 的目标已经完成：

- `Dify` 本地开发底座已跑通
- `FastAPI` 题目和接口范围已冻结
- `FastAPI` 最小可用链路已可运行
- `Dify` 候选 issue 已整理
- 第一个 Dify PR 切口已在本地准备好

Week 2 可以直接继续：

- 把 `Dify #33699` 整理成正式 PR
- 继续补 `FastAPI` 的任务链路、集成说明和版本管理
