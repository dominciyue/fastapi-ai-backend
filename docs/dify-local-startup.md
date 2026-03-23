# Dify 本地启动记录

## 目标

验证 `Dify` 开发所需中间件可以在本机稳定启动，并记录和当前 `FastAPI` 项目并行开发时的环境约束。

## 本次实际操作

仓库路径：

- `E:\Github高星项目\dify`

启动命令：

```bash
docker compose --env-file middleware.env -f docker-compose.middleware.yaml -p dify up -d
```

执行目录：

- `dify/docker`

## 已启动服务

- `db_postgres`
- `redis`
- `sandbox`
- `ssrf_proxy`
- `weaviate`
- `plugin_daemon`

## 实际可用状态

已确认：

- `Postgres` healthy，宿主机映射端口 `15432`
- `Redis` healthy，宿主机映射端口 `16379`
- `Weaviate` 可访问，`GET http://127.0.0.1:8080/v1/.well-known/ready -> 200`
- `plugin_daemon` 会在数据库尚未 ready 时短暂重启，随后可自行恢复

## 遇到的问题

首次启动失败，原因不是 `Dify` 配置本身，而是和 `fastapi-ai-backend` 的本地容器栈发生端口冲突：

- `5432`
- `6379`

## 解决方式

在 `dify/docker/middleware.env` 中显式错开端口：

- `EXPOSE_POSTGRES_PORT=15432`
- `EXPOSE_REDIS_PORT=16379`

同时必须使用：

```bash
docker compose --env-file middleware.env -f docker-compose.middleware.yaml -p dify up -d
```

不能省略 `--env-file middleware.env`，否则 compose 变量替换不会读取这份文件。

## 当前结论

- `Dify` 本地开发所需的中间件底座已经跑通
- 可以继续推进：
  - `api/.env` 配置
  - `uv sync --group dev`
  - API 进程本地启动
  - 后续把 `FastAPI RAG Tool Service` 作为外部能力接入
