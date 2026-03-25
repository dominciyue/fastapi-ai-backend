# Week 2 总结

## 本周目标

完成 `Dify + FastAPI` 双主线的第二阶段推进：

- 产出第一个真实的 `Dify` PR
- 收口 `FastAPI` 侧核心骨架与任务链路
- 把本地验证、仓库托管和阶段文档补齐到可继续进入 Week 3 的状态

## 本周完成了什么

### Dify 侧

- 放弃了已高度拥挤的 `#33699` 方向，避免提交低命中率的重复 PR
- 重新筛选出一个更稳的小修复切口：
  - `dev/start-docker-compose`
- 修复点包括：
  - 显式加载 `middleware.env`
  - 按 review 建议移除冗余 `--profile` 参数
- 已完成 PR：
  - `langgenius/dify#33927`
- 已完成首轮 review 跟进：
  - 更新脚本
  - 更新 `Test plan`
  - 回复 review comment

更完整的 Dify 侧过程见：

- `docs/dify-week2-review.md`

### FastAPI 侧

- 保持并确认 `FastAPI AI Backend` 主仓库已托管到：
  - `git@github.com:dominciyue/fastapi-ai-backend.git`
- 核心骨架已经收口为稳定结构：
  - `app/api`
  - `app/core`
  - `app/models`
  - `app/schemas`
  - `app/services`
  - `app/tasks`
- 核心任务链路已经具备完整主路径：
  - 上传文档：`POST /api/v1/documents/upload`
  - 创建索引任务：`POST /api/v1/documents/index`
  - 查询任务状态：`GET /api/v1/tasks/{task_id}`
  - 向量检索：`POST /api/v1/retrieval/search`
  - 同步问答：`POST /api/v1/chat/query`
  - 流式问答：`POST /api/v1/chat/stream`

### FastAPI 任务链路已经具备的关键能力

#### 1. 异步索引主链路

- API 侧负责接收上传、创建文档记录和索引任务
- `Celery` worker 负责后台执行解析、切片、embedding 和入库
- `Postgres + pgvector` 负责存储 chunk 与向量
- `Redis` 负责消息队列和结果后端

#### 2. 无 API Key 的本地演示能力

- `app/services/llm_client.py` 已支持 mock fallback
- 未配置真实模型 Key 时，仍可完成：
  - mock embedding
  - mock chat
  - mock stream chat

这保证了本地演示、录屏和面试讲解时不会被上游模型配置卡住。

#### 3. 本地验证工具

- 自动化测试：
  - `tests/test_chunker.py`
  - `tests/test_chat_service.py`
  - `tests/test_document_parser.py`
  - `tests/test_indexing_task.py`
  - `tests/test_llm_client.py`
  - `tests/test_retrieval_service.py`
- 冒烟脚本：
  - `scripts/smoke_upload.py`
  - `scripts/smoke_index.py`
  - `scripts/smoke_task.py`
  - `scripts/smoke_stream.py`

#### 4. 文档资产

- `docs/architecture.md`
- `docs/api-spec.md`
- `docs/db-schema.md`
- `docs/dify-integration.md`
- `docs/interview-notes.md`

## 本周额外完成的验证

本轮再次确认：

- `pytest`：`9` 个测试全部通过
- `ruff check .`：通过

这意味着 FastAPI 侧当前至少在本地静态检查和已有单测范围内是健康的。

## 当前结论

到 Week 2 结束时，两个主线都已经具备继续推进的基础：

- `Dify` 侧已经拿到第一个真实 PR，并完成首轮 review 跟进
- `FastAPI` 侧已经具备稳定的核心骨架、异步任务链路和本地验证手段

换句话说，Week 2 的目标已经完成，后续可以进入更偏“主链路打磨”和“集成收口”的阶段。

## Week 3 建议

下一步优先推进：

1. 做更完整的 FastAPI 主链路验证，重点围绕上传 -> 索引 -> 检索 -> 问答
2. 补充更贴近真实使用的接口测试或服务级测试
3. 准备把 `FastAPI` 服务真正接到 `Dify` 的 workflow / tool 调用场景里
