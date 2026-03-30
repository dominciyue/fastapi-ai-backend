# Week 4 总结

## 本周目标

推进 `FastAPI AI Backend` 与 `Dify` 的真实集成，重点完成：

- 明确 `Dify` 与 `FastAPI` 在同步接口和流式接口上的边界
- 让 `Dify` 能把本项目作为外部工具真正导入并调用
- 打通 `Dify -> 外部工具 -> FastAPI RAG 服务` 的联调链路

## 本周完成了什么

### 1. Dify 集成边界已经明确

本周先把一个容易混淆的问题确认清楚了：

- `FastAPI` 侧已经提供 `POST /api/v1/chat/stream`
- 但当前 `Dify` 的 HTTP Tool / Workflow HTTP Request Node 不适合直接消费外部上游 `SSE`

因此当前阶段的正确接法是：

- `Dify` 集成优先走同步接口：
  - `POST /api/v1/retrieval/search`
  - `POST /api/v1/chat/query`
- `POST /api/v1/chat/stream` 继续保留给原生前端、脚本或自定义客户端直接使用

这一步已经同步体现在：

- `README.md`
- `docs/dify-integration.md`
- `integrations/dify-tool.openapi.yaml`

### 2. Dify 可导入的 OpenAPI 资产已经补强

为了让外部工具导入更稳定，本周补强了 `OpenAPI` 描述：

- 明确只暴露同步检索和同步问答能力
- 补齐 `servers`
- 补齐 `components/schemas`
- 补齐请求示例
- 补齐返回结构说明

当前 `Dify` 导入使用的文件是：

- `integrations/dify-tool.openapi.yaml`

### 3. Dify 本地完整应用已成功拉起

本周不仅启动了 `middleware`，还把 `Dify` 的完整应用层拉起来了。

本地访问地址：

- `http://127.0.0.1:18080`

为了避免与现有本地服务冲突，这次联调增加了一个本地专用配置文件：

- `dify/docker/.env`

它目前只用于本地调试，主要作用有两类：

- 调整 `nginx`、`plugin_daemon` 等宿主机暴露端口
- 让 `Dify` 应用层复用已经单独跑起来的 `middleware`

当前本地联调实际复用的是：

- `Postgres -> host.docker.internal:15432`
- `Redis -> host.docker.internal:16379`
- `Weaviate -> host.docker.internal:8080`

### 4. Dify 管理员初始化已经完成

本周已经完成 `Dify` 自托管环境初始化：

- 管理员账号已创建
- `Dify API` 可正常响应 `console/api` 路径
- 后续已经具备继续进入工具管理和 workflow 编排的条件

### 5. 外部工具已经成功导入 Dify

本周已经把 `FastAPI` 服务作为外部 API Tool 成功导入到 `Dify`。

导入后的 provider 名称是：

- `fastapi_rag_tool_service`

`Dify` 侧已正确解析出两个工具：

- `retrievalSearch`
- `chatQuery`

### 6. 实际联调已经通过

这一步不是只停留在“导入成功”，而是已经通过 `Dify` 的接口预检能力做了真实调用验证。

已经验证通过：

- `retrievalSearch` 可以从 `Dify` 成功调用到 `FastAPI` 的检索接口
- `chatQuery` 可以从 `Dify` 成功调用到 `FastAPI` 的问答接口

这意味着当前已经打通：

- `Dify -> 外部工具(OpenAPI) -> FastAPI RAG 服务`

### 7. 最小 Workflow DSL 已经落地并跑通

在外部工具导入成功之后，本周继续补了一份可直接导入的最小 workflow DSL：

- `integrations/dify-rag-workflow.yml`

这份 DSL 对应的是一条最小链路：

1. `Start`
2. `retrievalSearch`
3. `chatQuery`
4. `End`

其中：

- `retrievalSearch` 负责调用 `FastAPI` 的检索接口
- `chatQuery` 负责调用 `FastAPI` 的同步问答接口
- `End` 节点输出最终回答文本

本轮已经完成：

- workflow DSL 导入 `Dify`
- workflow draft 拉取校验
- 单节点调试
- 整条 workflow draft 运行
- workflow 输出结构优化

最终结果是：

- workflow 导入成功
- `retrieval_node` 单节点运行成功
- 完整 workflow draft 运行成功
- 最终 `workflow_finished.status = succeeded`
- 最终输出已从单个 JSON 字符串优化为：
  - `final_output`
  - `answer`
  - `sources`

这说明当前已经进一步打通：

- `Dify Workflow -> API Tool -> FastAPI RAG 服务`

## 遇到的问题

### 1. Dify 完整应用和现有本地服务端口冲突

现象：

- `plugin_daemon`
- `redis`
- `weaviate`

这些服务的默认宿主机端口会与现有开发环境冲突。

处理：

- 增加本地 `dify/docker/.env`
- 只覆盖本地暴露端口
- 不改上游默认 compose 文件

### 2. Dify 应用层默认连不到独立 middleware

现象：

- `api` 启动时找不到默认的 `db_postgres`
- `nginx` 首页能打开，但 `console/api/*` 返回 `502`

处理：

- 把 `Dify` 应用层显式改为连接已经启动的外部 middleware
- 使用 `host.docker.internal` 指向宿主机暴露端口

### 3. 登录和调用控制台接口时有格式要求

现象：

- 登录接口直接发明文密码会失败
- 已登录状态下调用控制台写接口会因 `CSRF` 失败

处理：

- 登录密码按前端逻辑做 `Base64`
- 后续控制台请求带上 `X-CSRF-Token`

### 4. Dify 当前不适合直接消费外部 SSE

现象：

- `FastAPI` 流式接口已存在
- 但当前 `Dify` 的外部 HTTP 工具主路径不适合直接使用上游 `SSE`

处理：

- 将 `Dify` 集成主路径收敛到同步接口
- 把流式能力保留给独立客户端

## 本地存储占用说明

本周还额外确认了 `Docker` 当前的本机占用情况。

当前大致情况：

- `Images`：约 `13.26GB`
- `Containers`：约 `4.52GB`
- `Local Volumes`：约 `83MB`
- `Build Cache`：约 `367MB`

其中 `Dify` 相关镜像里，体积较大的主要是：

- `langgenius/dify-api:1.13.2`：约 `2.92GB`
- `langgenius/dify-plugin-daemon:0.5.4-local`：约 `1.54GB`
- `langgenius/dify-sandbox:0.2.12`：约 `578MB`
- `langgenius/dify-web:1.13.2`：约 `340MB`

这说明：

- `Dify` 本地联调确实会明显占用磁盘
- 但当前真正大的主要是镜像和停止后的容器层，不是数据卷

如果后续要回收空间，优先顺序建议是：

1. 删除无用停止容器：`docker container prune`
2. 删除无用构建缓存：`docker builder prune`
3. 删除悬空镜像：`docker image prune`
4. 如果确认某些整套环境不再需要，再做更大范围清理：`docker system prune -a`

注意：

- 不要随便删除仍在使用的数据卷
- 如果要清理 `FastAPI` 或 `Dify` 的数据库数据，必须确认当前是否还需要保留本地测试数据

## 哪些内容不能推远端

这次联调里，有一类内容只适合留在本地，不应该推到远端仓库：

- `dify/docker/.env`
- 任何包含本地端口映射的临时联调配置
- 本地管理员账号相关信息
- 含密钥、口令或本机网络拓扑信息的配置文件

原因很明确：

- 这些配置是你当前机器的本地运行解法
- 不是上游仓库或通用开发环境的标准默认值
- 一旦提交，容易把个人本地环境和共享代码混在一起

从当前状态看：

- `dify` 仓库 `git status` 仍然是干净的
- 说明这类本地联调文件当前没有进入版本控制

所以这部分不应该推到远端上游，也不应该混进后续正式 PR。

## 当前结论

到目前为止，Week 4 已经完成了关键主链路：

- `FastAPI` 到 `Dify` 的工具级接入已经跑通
- `Dify` 已能真实调用本项目的检索和问答接口
- 最小 workflow 已可导入并成功运行
- 集成边界、导入资产和本地联调方式都已经明确

但还有一部分工作留待下一轮继续：

- 继续做更贴近演示场景的 workflow 编排
- 决定是否把回答结果进一步结构化，而不是直接输出工具返回的 JSON 字符串
- 决定是否补一版更正式的联调录屏、截图或操作说明

## 下一步建议

晚上继续时，建议优先按这个顺序推进：

1. 优化现有 workflow，让 `End` 节点输出更适合直接展示的结构化结果
2. 再补一条更接近演示场景的 workflow 版本
3. 视情况把 `Week 4` 文档收口为“已完成”状态
