# Docker 部署

## 部署模式

仓库当前提供两套运行方式：

- `docker-compose.yml`
  - 偏开发环境，`api` 默认带 `--reload`
- `docker-compose.prod.yml`
  - 偏稳定演示或交付环境，关闭热重载并补上重启策略与 `readiness` 检查

如果你只是本地开发，使用基础 compose 即可。

如果你要做录屏、联调、答辩或更稳定的演示，建议叠加生产覆盖文件。

## 前置条件

- 已安装 `Docker Desktop`
- 本机可正常执行 `docker compose`
- 已复制 `.env.example` 为 `.env`

```bash
cp .env.example .env
```

## 推荐启动命令

### 开发模式

```bash
docker compose up --build
```

### 稳定演示 / 交付模式

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

## 服务组成

启动后会拉起以下组件：

- `api`
- `worker`
- `postgres`
- `redis`

其中：

- `api` 提供 HTTP 接口
- `worker` 处理异步索引
- `postgres` 保存业务数据与向量
- `redis` 提供缓存和任务队列

## 状态检查

启动后可执行：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

如果你使用的是开发模式，也可以直接执行：

```bash
docker compose ps
```

## 停止服务

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

## 重建数据卷

只有在以下场景才建议删除数据卷：

- 测试数据可以丢弃
- 需要重建向量维度
- 需要重置数据库状态

执行方式：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v
```

## 部署建议

- 演示前优先使用生产覆盖文件，避免 `--reload` 带来的不稳定性
- 切换 embedding 提供方前先确认实际向量维度
- 首次启动后先做一轮完整冒烟验证，再接上层平台

## 相关文档

- 验证流程：`verification.md`
- 故障排查：`troubleshooting.md`
- 配置说明：`../configuration.md`
