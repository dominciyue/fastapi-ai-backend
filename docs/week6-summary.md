# Week 6 总结

## 本周目标

Week 6 的重点不再是继续扩展最小可用功能，而是把已经跑通的 `FastAPI AI Backend` 进一步补强成一个更像真实 AI 后端服务的工程样本。

这一周的工作主线可以概括为六轮增强：

- 检索缓存
- 轻量 rerank
- 请求追踪与 metrics
- 上下文与回答长度约束
- chat usage 观测与测试体系规范化
- 错误模型标准化与调用方 warnings

相比 Week 5 更偏工程化收口，Week 6 更强调的是：

- 提升接口返回的可观测性
- 提升调用方可感知的链路信息
- 降低重复请求成本
- 为 Dify 集成和后续面试讲解补足“服务端细节”

## 本周完成了什么

### 1. 第一轮增强：补上 Redis 检索缓存

本轮新增了：

- `app/services/cache.py`
- `ENABLE_RETRIEVAL_CACHE`
- `RETRIEVAL_CACHE_TTL_SECONDS`

核心变化是把检索结果做了 Redis 级缓存，让相同 query 在命中缓存时，不必重复走 embedding 请求和向量检索。

这一步带来的价值很直接：

- 降低重复问答的成本
- 提升热门 query 的响应速度
- 更符合真实 RAG 服务中“检索层先做轻缓存”的常见做法

现在检索响应里已经能看到：

- `meta.cache_hit`

这让上层调用方可以明确知道当前结果是否来自缓存。

### 2. 第二轮增强：加入轻量关键词 rerank

本轮补了：

- `ENABLE_KEYWORD_RERANK`
- `RERANK_CANDIDATE_MULTIPLIER`
- 请求级 `rerank` 开关

实现策略不是引入独立 reranker 模型，而是在向量召回后，基于 query 与 chunk 文本的关键词重叠做一次本地轻量重排。

这样做的原因很明确：

- 开发成本低
- 讲解成本低
- 能体现“先召回再重排”的完整检索思路
- 适合当前项目阶段，不会过早把复杂度拉高

现在检索和问答接口都已经支持：

- 请求体传 `rerank`
- 响应 `meta` 返回 `reranked`
- 响应 `meta` 返回 `candidate_count`

这让 rerank 行为不仅能开关，还能被上层清楚观测。

### 3. 第三轮增强：补上 request_id、响应耗时和轻量 metrics

本轮新增了：

- 请求级 `X-Request-ID`
- 响应头 `X-Response-Time-Ms`
- 进程内 `MetricsStore`
- `GET /metrics`

这轮的重点是让接口从“只返回业务数据”提升到“同时带上链路和观测信息”。

当前已经具备的能力包括：

- 每个请求自动注入 `request_id`
- 返回体 `meta` 中透出 `request_id`
- 响应头返回接口耗时
- `/metrics` 汇总 HTTP、retrieval、chat 三级统计

对外讲这部分时，可以很自然地说明：

- 如何定位一次请求
- 如何观察错误数和耗时
- 如何看到缓存命中与 rerank 发生次数

### 4. 第四轮增强：补上上下文长度和回答长度约束

本轮新增了：

- `MAX_CONTEXT_CHARACTERS`
- `MAX_ANSWER_TOKENS`
- 请求级覆盖参数：
  - `max_context_characters`
  - `max_answer_tokens`

这轮增强解决的是“LLM 输入和输出不受控”的问题。

现在 chat 接口已经支持：

- 控制拼接给模型的上下文最大字符数
- 控制下游 chat model 的 `max_tokens`
- 在返回体中显式告诉调用方本次上下文长度与回答上限

这类能力对接 Dify 或其他外部客户端时尤其有用，因为它能把“模型调用边界”从服务内部逻辑抬升到接口协议层。

### 5. 第五轮增强：补上 chat usage 观测并规范测试体系

本轮新增或完善了：

- chat 维度 metrics
- token usage estimate
- `tests/conftest.py`
- `tests/test_metrics_store.py`
- `tests/test_llm_client.py`

其中最关键的增强有两块：

第一块是 chat 观测信息更完整了：

- `prompt_tokens_estimate`
- `completion_tokens_estimate`
- `total_token_estimate`
- `average_context_characters`
- `context_truncations`

第二块是测试规范化：

- 统一在 `conftest.py` 中清理 `metrics_store`
- 统一清理 `dependency_overrides`
- 给 metrics、LLM 请求参数透传等逻辑补上更聚焦的单测

这让测试不再只是“接口能不能通”，而是开始覆盖：

- metrics 是否聚合正确
- max token 参数是否真的传给模型层
- 流式问答完成后 metrics 是否会落账

### 6. 第六轮增强：标准化错误返回并增加 warnings

本轮补的是更偏“接口契约质量”的内容，包括：

- `AppError` 增加 `error_code`
- `AppError` 增加 `retryable`
- `RequestValidationError` 统一收口
- `RetrievalMeta.warnings`
- `ChatMeta.warnings`

现在错误返回不再只有一个 `detail`，而是统一带上：

- `detail`
- `error_code`
- `retryable`
- `request_id`

这样上层调用方就能更清楚地区分：

- 是参数校验错误
- 还是业务错误
- 是否值得重试
- 该用哪个 `request_id` 去排查

与此同时，成功返回里也增加了 `warnings`，用于告诉调用方一些“请求虽然成功，但结果需要注意”的情况，例如：

- 检索命中数少于请求数
- 上下文被截断
- 无检索来源时仍生成回答

这类返回非常适合和 Dify 这类外部编排平台对接，因为它把很多“隐性降级”变成了“显式信号”。

## 本周完整测试结果

本次在本地实际完成了容器级联调测试，而不是只跑单元测试。

### 1. 容器启动验证

实际执行了：

- `docker compose up -d --build`

确认本地以下服务成功启动：

- `api`
- `worker`
- `postgres`
- `redis`

### 2. 主链路冒烟验证

实际执行了：

- `python scripts/smoke_all.py --timeout 180 --interval 2`

完整验证了以下流程：

1. `GET /health/ready`
2. `POST /api/v1/documents/upload`
3. `POST /api/v1/documents/index`
4. `GET /api/v1/tasks/{task_id}`
5. `POST /api/v1/retrieval/search`
6. `POST /api/v1/chat/query`
7. `POST /api/v1/chat/stream`

验证结果：

- 主链路通过
- 异步索引通过
- 检索返回正常
- 同步问答返回正常
- SSE 流式返回正常

### 3. Week 6 增强项专项回归

除主链路外，还额外验证了以下能力：

- 检索接口支持 `rerank=false`，并能正确返回 `meta.reranked = false`
- chat 接口支持 `max_context_characters` 和 `max_answer_tokens`
- 当上下文被截断时，`meta.context_truncated = true`
- 当上下文被截断时，`meta.warnings` 会返回提示
- 检索命中数少于请求值时，`meta.warnings` 会返回提示
- 非法参数会返回标准化 `422` 错误体
- `/metrics` 能返回 HTTP、retrieval、chat 三类统计信息
- 响应头会返回 `x-request-id` 与 `x-response-time-ms`
- 检索缓存命中后，`meta.cache_hit = true`

### 4. 测试结论

从本次完整联调结果看，Week 6 六轮增强涉及的核心接口能力都已经正常工作，未发现需要立即修复的功能性 bug。

当前可以明确认为以下能力已经稳定可用：

- Redis 检索缓存
- 轻量关键词 rerank
- 请求级追踪
- 响应耗时头
- `/metrics` 观测入口
- 上下文与回答长度限制
- chat token usage 估算
- 标准化错误返回
- 调用方 warnings 机制

## 本周发现的一个收尾项

虽然接口本身已经通过联调，但在本轮检查中也发现一个非代码逻辑问题：

- `docs/api-spec.md`
- `integrations/dify-tool.openapi.yaml`

这两份文档资产目前还没有完全同步 Week 6 新增的字段，例如：

- `meta`
- `warnings`
- `rerank`
- `max_context_characters`
- `max_answer_tokens`
- 标准化错误结构

这不会影响当前服务运行，但会影响后续文档展示和 Dify 工具说明的一致性，适合作为 Week 6 收尾后的下一步文档补强项。

## 当前结论

Week 6 的六轮增强已经基本完成，并且已经通过一轮真实容器环境下的完整联调验证。

如果说 Week 3 到 Week 4 解决的是“RAG 主链路能不能跑通”，Week 5 解决的是“项目有没有工程化外壳”，那么 Week 6 解决的就是：

- 接口是不是更像真实服务
- 返回是不是更适合上层系统消费
- 链路是不是更可观测
- 异常和降级是不是更可解释

经过这一轮补强后，这个项目已经不只是一个能演示上传、索引、检索、问答的 demo，而是一个更适合拿去讲“AI 后端工程设计细节”的样本项目。

## 下一步建议

Week 6 收口后，更适合继续推进的方向有两类：

1. 同步更新 `docs/api-spec.md` 和 `integrations/dify-tool.openapi.yaml`，让文档资产跟上接口实际能力
2. 如果还要继续增强，可以进入更偏平台化的方向，例如更完整的 tracing、后台任务可观测性、鉴权或更真实的 reranker 接入
