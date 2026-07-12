# Month 01 Roadmap：Mini Agent Harness 工程基础

## 1. 本月目标

本月的目标是建立 Mini Agent Harness 的工程基础，而不是实现完整的 Agent 产品。

月底时，项目应具备：

- 规范的 Python 工程目录
- 统一配置管理
- 统一日志与异常体系
- DeepSeek API 非流式和流式调用
- 最小工具注册与执行机制
- 最小 Agent Loop
- 基础单元测试与集成测试
- 固定评测任务
- 完整的 README 和本地运行方法

## 2. 工程原则

- 使用 `pyproject.toml`
- 使用 `src/` layout
- 使用完整类型标注
- 使用 `pytest`
- 使用 `ruff`
- 使用 `mypy`
- 使用 `pydantic-settings`
- 配置、日志、模型调用、工具系统和 Agent Loop 分离
- 当前阶段不使用 LangChain 或 LangGraph
- 不为了未来需求提前设计复杂抽象
- 每项功能必须定义验收条件

## 3. 每周安排

### Week 1：项目工程基础

目标：

- 初始化仓库和 Python 环境
- 建立目录结构
- 配置依赖和质量工具
- 实现配置加载
- 实现日志和自定义异常
- 为配置模块编写测试

完成标准：

- `pytest` 通过
- `ruff check .` 通过
- `ruff format --check .` 通过
- `mypy src` 通过
- 项目可以从命令行启动

### Week 2：LLM Client

目标：

- 理解 DeepSeek API 请求格式
- 定义模型客户端边界
- 实现非流式调用
- 实现流式调用
- 处理超时、限流和服务端错误
- 使用 Mock 编写测试

完成标准：

- 能在终端完成一次对话
- 支持流式输出
- 不在测试中真实消耗 API
- 网络异常能转换为项目自定义异常

### Week 3：Tool System 与 Agent Loop

目标：

- 定义工具接口
- 实现 Tool Registry
- 实现 list_files
- 实现 read_file
- 实现 search_text
- 接入 Tool Calling
- 实现最小 Agent Loop
- 增加最大步骤限制

完成标准：

- Agent 能根据任务主动读取项目文件
- 非法路径被拒绝
- `.env` 等敏感文件不能被读取
- 工具参数错误能被识别
- Agent 不会无限循环

### Week 4：Tracing、Evaluation 与交付

目标：

- 记录 Agent 执行轨迹
- 创建 20 条固定测试任务
- 实现基础评测脚本
- 分析至少三个 Badcase
- 完善 README
- 发布 v0.1.0

完成标准：

- 能输出任务成功率
- 能统计步骤、延迟和 Token
- 有可重复运行的评测任务
- 有架构说明和运行说明
- 有清晰的已知限制

## 4. 本月暂时不做

- Multi-Agent
- MCP
- 长期记忆
- RAG
- 向量数据库
- 浏览器自动化
- 任意 Shell 执行
- 完整桌面 UI
- 模型微调
- 复杂数据库
- 微服务拆分

## 5. 月末验收

月底时，我应该能够完整解释：

1. 用户输入如何变成模型请求。
2. 模型客户端为什么与 Agent Loop 分离。
3. 模型如何请求工具，以及程序如何执行工具。
4. 为什么不能信任模型生成的工具参数。
5. 如何处理超时、限流和异常。
6. 如何通过测试和固定任务判断系统是否变好。