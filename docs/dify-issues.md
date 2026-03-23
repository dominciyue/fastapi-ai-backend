# Dify 候选贡献点

## 当前筛选原则

- 优先小而稳
- 优先后端、配置、状态接口或测试类问题
- 避免一上来碰大功能和复杂前端改动

## 已确认的候选 issue

### 第一优先级

1. `#33699` `[Refactor/Chore] bump pyrefly version`
   - 类型：依赖升级 / chore
   - 优点：范围小、风险低、容易验证
   - 当前进展：已在本地将 `api/pyproject.toml` 中的 `pyrefly` 从 `>=0.55.0` 提升到 `>=0.57.0`，并用 `uv lock --upgrade-package pyrefly` 更新到 `0.57.1`
   - 判断：最适合作为第一个 Dify PR

2. `#33439` `[Refactor/Chore] bad-argument-type in test_queue_integration.py`
   - 类型：类型检查修复
   - 优点：后端测试文件，影响范围可控
   - 风险：需要确认当前主干是否已局部修复或存在关联改动
   - 判断：可作为第一个 PR 的备选或第二个 PR

### 第二优先级

3. `#33092` `[Refactor/Chore] replace json.load by pydantic`
   - 类型：重构
   - 优点：偏后端、可讲工程规范
   - 风险：触点可能跨多个模块，首个 PR 稍大

4. `#32863` `[Refactor/Chore] migrate to TypedDict`
   - 类型：类型系统增强
   - 优点：有助于展示 Python 类型工程能力
   - 风险：容易扩散到多个调用点

5. `#32494` `[Refactor/Chore] No matching overload found for function`
   - 类型：类型检查修复
   - 优点：通常改动小
   - 风险：需要先定位对应文件和复现方式

6. `#32454` `[Refactor/Chore] use Testcontainers to do sql test`
   - 类型：测试工程
   - 优点：和当前 AI 后端路线贴近，面试可讲测试隔离
   - 风险：本地验证成本高于简单 chore

### 第三优先级

7. `#31572` `[Refactor/Chore] Split the environment configuration files to make docker compose clean again.`
   - 类型：配置整理
   - 优点：契合我们当前已观察到的 Docker 环境复杂度
   - 风险：可能触及多个 compose 文件，适合第二阶段

8. `#31497` `[Refactor/Chore] avoid pass dict, directly pass basemodel`
   - 类型：代码整洁度 / schema 收敛
   - 优点：和 `FastAPI + Pydantic` 主线一致
   - 风险：可能涉及较多调用方

## 本地环境观察

- `dify/docker/middleware.env.example` 默认暴露 `5432` 与 `6379`
- 当本机同时运行 `fastapi-ai-backend` 的 `Postgres + Redis` 时，会发生端口冲突
- 使用 `docker compose --env-file middleware.env -f docker-compose.middleware.yaml -p dify up -d` 可正确读取自定义端口
- `plugin_daemon` 在数据库尚未 ready 时会短暂重启，随后恢复，属于可接受的启动阶段现象

## 当前判断

- 之前公开提到的 `ENFORCE_LANGGENIUS_PLUGIN_SIGNATURES` 缺失问题在当前版本中已存在，不适合作为首个贡献点
- 当前最稳妥路线：
  - 先推进 `#33699`
  - 若需要第二个 PR，再看 `#33439` 或其他类型检查 / 测试修复 issue
