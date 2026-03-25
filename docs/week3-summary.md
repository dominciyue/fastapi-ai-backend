# Week 3 总结

## 本周目标

完成 `FastAPI AI Backend` 在 Week 3 的主线收口：

- 打通上传 -> 索引 -> 检索 -> 问答的最小可用 `RAG` 链路
- 把 `chat` 与 `embedding` 从“可 mock 演示”推进到“真实模型接入”
- 解决真实 embedding 落地时的配置、维度和数据库兼容问题

## 本周完成了什么

### 1. 真实模型接入策略明确

本周先确认了一个关键事实：

- `DeepSeek` 目前适合继续承担聊天模型
- 当前使用的 `DeepSeek` 账号没有可直接使用的 embedding 模型
- 直接请求 `https://api.deepseek.com/v1/embeddings` 会返回 `404`

因此项目最终采用了拆分方案：

- `chat`：`DeepSeek`
- `embedding`：`阿里云百炼 DashScope`

这也验证了当前服务把聊天模型和 embedding 模型拆开配置是必要的。

### 2. 真实 embedding 已接入并验证可用

当前本地联调配置已经跑通：

- `CHAT_BASE_URL=https://api.deepseek.com/v1`
- `CHAT_MODEL=deepseek-chat`
- `EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`
- `EMBEDDING_MODEL=text-embedding-v3`
- `EMBEDDING_DIMENSION=1024`

为了降低切换提供方时的试错成本，本周还补了一个独立检查脚本：

- `scripts/check_embedding_provider.py`

它可以在真正开始索引前，先检查：

- 当前是 `mock` 还是 `real` 模式
- embedding 服务地址
- embedding 模型名
- 配置维度
- 实际返回维度

### 3. 主链路的稳定性做了针对性补强

围绕真实 embedding 接入，本周补了两类关键保护：

第一类是 embedding 侧的失败前置：

- 在 `app/services/llm_client.py` 中增加维度校验
- 如果配置的 `EMBEDDING_DIMENSION` 和实际返回维度不一致，会直接抛出清晰错误
- 对 `404` 场景补充了更明确的错误提示，方便快速判断是模型不存在还是接口不兼容

第二类是索引事务侧的失败收口：

- 在 `app/services/indexing.py` 中补了 `rollback`
- 当索引写库阶段失败时，会把文档状态更新为 `failed`
- 同时保证任务状态也能正确标记失败，而不是把数据库留在半完成状态

### 4. 数据库结构已与真实 embedding 维度对齐

接入 `DashScope` 后确认其返回向量维度是：

- `1024`

而此前本地库里 `pgvector` 列维度还是旧值：

- `1536`

由于 `pgvector` 列维度是表结构级别固定的，本周按测试环境处理方式直接完成了：

- 销毁旧容器数据卷
- 重建本地数据库
- 重新初始化 `vector(1024)` 结构

这一步做完后，真实 embedding 才能稳定写入索引表。

## 遇到的问题

### 1. DeepSeek 不提供当前需要的 embedding 能力

现象：

- chat 可以用
- embeddings 接口返回 `404`

处理：

- 不再强行把 `DeepSeek` 当作 embedding 提供方
- 保留 `DeepSeek` 做 chat
- 单独接入 `DashScope` 做 embedding

### 2. 模型维度与数据库 schema 不匹配

现象：

- embedding 服务真实返回 `1024` 维向量
- 本地数据库仍是旧的 `vector(1536)`

处理：

- 在代码里增加维度校验，先让错误尽早暴露
- 然后重建本地数据库，让 schema 和真实模型对齐

### 3. 索引失败时需要保证状态一致性

现象：

- 如果在 chunk 入库阶段失败，任务状态和文档状态可能无法正确收口

处理：

- 补事务回滚
- 失败后重新拉取文档对象并写回 `failed`
- 增加测试覆盖回滚分支

## 本周验证结果

本周已经完成以下验证：

- `scripts/check_embedding_provider.py` 已确认当前 embedding 提供方返回真实 `1024` 维向量
- `pytest tests/test_llm_client.py tests/test_indexing_service.py`：通过
- 真实主链路冒烟验证：通过

本轮真实冒烟覆盖了：

- 文档上传
- 创建索引任务
- 查询任务状态
- 向量检索
- 同步问答
- 流式问答

当前主链路状态可以概括为：

- 真实 chat：已通
- 真实 embedding：已通
- 最小可用 `RAG` 主链路：已通

## 当前结论

Week 3 的核心目标已经基本达成：

- `FastAPI` 服务不再只是 mock 演示版
- 已具备真实 chat + 真实 embedding 的本地可运行链路
- 与 Week 4 的 `Dify` 集成之间，已经没有“模型接不通”这个前置阻塞项

换句话说，下一步可以把重心从“单服务主链路打通”切到“外部集成和产品化演示”。

## Week 4 建议

下一步优先推进：

1. 把 `FastAPI` 服务按 `OpenAPI` 或 HTTP Tool 方式正式接入 `Dify`
2. 用 `Dify Workflow` 实测一次检索和问答链路
3. 继续打磨流式输出体验、错误提示和联调文档
