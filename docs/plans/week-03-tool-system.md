# Week 03：Tool System 与最小 Agent Loop

## 1. 本周目标

在 Week 02 已完成的 LLM Client 基础上，让模型从“只能生成文本”升级为“能够请求程序执行工具，并根据工具结果继续完成任务”。

本周结束时，项目应具备：

- 清晰、可测试的 Tool 抽象
- Tool Registry
- 工具参数定义与验证
- 三个只读本地工具：
  - `list_files`
  - `read_file`
  - `search_text`
- 安全的工作目录边界
- 模型 Tool Calling 请求的解析
- 工具执行结果回传模型
- 最小 Agent Loop
- 最大 Agent 步数限制
- 工具错误的结构化处理
- 覆盖正常路径、失败路径和安全边界的测试

本周重点是理解这条核心链路：

    用户输入
        ↓
    Agent Loop
        ↓
    LLM Client
        ↓
    模型返回文本或 Tool Call
        ↓
    参数验证
        ↓
    程序执行工具
        ↓
    工具结果写回消息历史
        ↓
    再次请求模型
        ↓
    最终回答

本周不追求复杂 Agent 能力，只实现一个职责清晰、行为可控的最小闭环。

---

## 2. 前置条件

开始 Week 03 前，应确认 Week 02 已经完成：

- LLM 层已有清晰的数据模型
- 非流式模型请求可以工作
- 流式模型请求可以工作
- 网络错误已经转换为项目内部异常
- API Key 不会写入日志或异常信息
- 自动化测试不会真实访问模型 API
- HTTP Client 生命周期处理正确
- `pytest`、`ruff` 和 `mypy` 已配置并通过
- 至少完成一次真实 API Smoke Test

开始前运行：

    pytest
    ruff check .
    ruff format --check .
    mypy src

如果 Week 02 的基础检查仍然失败，应先修复，不要同时修改 LLM Client 和 Agent Loop。

---

## 3. 本周工程边界

本周涉及三个主要模块：

### Tool System

负责：

- 定义工具名称、描述和参数
- 注册和查找工具
- 验证工具调用参数
- 执行具体工具
- 返回统一的执行结果
- 将底层错误转换为 Tool 层错误

### Tool Calling Adapter

负责：

- 将内部 Tool 定义转换为模型 API 支持的工具格式
- 将模型返回的 Tool Call 转换为项目内部结构
- 保持供应商 API 格式与核心 Agent 逻辑隔离

### Agent Loop

负责：

- 保存当前运行所需的消息历史
- 调用模型
- 判断模型返回的是最终回答还是工具请求
- 调用 Tool Registry 执行工具
- 将工具结果追加到消息中
- 控制最大运行步数
- 在完成、失败或达到上限时退出

---

## 4. 各模块不应承担的职责

### Tool System 不应负责

- 决定 Agent 下一步做什么
- 直接调用模型
- 管理完整聊天会话
- 自动修改 Prompt
- 保存长期记忆
- 控制 UI

### Agent Loop 不应负责

- 直接访问文件系统
- 包含每个具体工具的业务逻辑
- 直接拼装供应商专有 HTTP JSON
- 管理长期记忆
- 执行任意 Shell 命令
- 实现复杂 Planning
- 进行 RAG 检索

### LLM Client 不应负责

- 直接执行工具
- 决定 Agent 是否结束
- 管理工具注册
- 判断文件路径是否安全

---

## 5. 建议目录结构

本周结束后，项目结构可以接近：

    src/
    └── mini_agent/
        ├── agent/
        │   ├── __init__.py
        │   ├── loop.py
        │   └── models.py
        │
        ├── llm/
        │   ├── __init__.py
        │   ├── base.py
        │   ├── models.py
        │   └── deepseek_client.py
        │
        ├── tools/
        │   ├── __init__.py
        │   ├── base.py
        │   ├── models.py
        │   ├── registry.py
        │   ├── list_files.py
        │   ├── read_file.py
        │   └── search_text.py
        │
        ├── config.py
        ├── exceptions.py
        ├── logger.py
        └── main.py

    tests/
    ├── agent/
    │   └── test_loop.py
    │
    ├── llm/
    │   └── ...
    │
    └── tools/
        ├── test_registry.py
        ├── test_list_files.py
        ├── test_read_file.py
        └── test_search_text.py

这只是建议边界。

不要为了匹配目录树而创建：

- 没有实际内容的抽象层
- 只转发一个函数的包装模块
- 复杂工厂
- 依赖注入容器
- 通用插件框架

实际目录应根据当前代码结构调整。

---

# Task 1：定义 Tool Contract 与 Tool Registry

状态：未开始

## 目标

建立所有工具共享的最小契约，使 Agent Loop 不需要知道每个具体工具如何实现。

需要表达：

- 工具名称
- 工具描述
- 参数 Schema
- 工具执行入口
- 工具执行结果
- 工具调用错误

## 需要解决的问题

如果 Agent Loop 使用如下方式直接判断工具：

    if tool_name == "read_file":
        ...
    elif tool_name == "list_files":
        ...

随着工具数量增加，会出现：

- Agent Loop 与具体工具强耦合
- 每新增一个工具都要修改核心循环
- 工具难以独立测试
- 工具描述和执行逻辑容易分散
- 重名工具难以发现
- 不存在的工具难以统一处理

因此需要一个轻量级 Tool Registry。

## 推荐最小模型

可以考虑定义：

- `ToolCall`
- `ToolResult`
- `Tool`
- `ToolRegistry`

### ToolCall

表达模型请求执行什么工具：

- Tool Call ID
- 工具名称
- 参数

不要直接在整个项目中传递供应商原始 Tool Call JSON。

### ToolResult

至少表达：

- Tool Call ID
- 工具名称
- 是否成功
- 文本输出
- 错误信息

是否需要独立的错误字段，应根据当前消息模型决定。

### Tool

最小职责：

- 暴露名称
- 暴露描述
- 暴露参数 Schema
- 执行已经通过基础解析的参数

当前可以使用：

- `Protocol`
- `ABC`
- 普通基类

开始实现前应根据项目现状讨论取舍。

不要为了未来未知需求建立复杂继承体系。

### ToolRegistry

最小能力：

- 注册工具
- 根据名称获取工具
- 列出已注册工具
- 拒绝重复工具名
- 在工具不存在时提供明确错误

当前不需要：

- 自动扫描目录
- 动态加载第三方插件
- 运行时卸载插件
- 工具版本管理
- 远程工具注册

## 参数验证

工具参数来自模型输出，属于不可信输入。

必须处理：

- 缺少必填字段
- 多余字段
- 类型错误
- 空字符串
- 非法路径
- 无效数值范围

可以使用项目已有的数据验证方案。

不应让具体工具内部到处手动执行无结构的：

    arguments["path"]

## 验收条件

- Agent Loop 可以只依赖 Tool 接口和 Registry
- Registry 能注册并查找工具
- 重复工具名被拒绝
- 不存在的工具返回明确错误
- 工具参数有结构化验证
- Tool Call 与供应商原始 JSON 解耦
- `mypy src` 通过
- Registry 具有独立单元测试

## 测试场景

- 注册一个合法工具
- 根据名称查找工具
- 列出所有工具
- 注册重复名称
- 查找不存在的工具
- 工具名称为空
- 参数合法
- 参数缺失
- 参数类型错误
- 多余参数如何处理

## 本任务暂时不做

- 文件系统工具
- Tool Calling API 对接
- Agent Loop
- Shell 工具
- MCP
- 工具权限系统
- 动态插件发现
- 并行工具执行

## 建议 Commit

    feat: define tool contracts and registry

---

# Task 2：实现安全的只读文件工具

状态：未开始

## 目标

实现三个最小工具：

- `list_files`
- `read_file`
- `search_text`

这些工具只允许读取配置的项目工作目录，不允许访问任意系统文件。

---

## 2.1 统一工作目录边界

在实现工具前，先明确 Workspace Root。

例如：

    /path/to/mini-agent-harness

工具接收到的路径应被解释为 Workspace Root 下的相对路径。

不应默认允许：

- 任意绝对路径
- `../` 逃离工作目录
- 通过符号链接逃离工作目录
- 读取 `.env`
- 读取私钥、Token 或凭据文件
- 读取超大文件
- 读取二进制文件

路径安全逻辑应尽可能复用，但不要创建过度通用的文件系统框架。

## 2.2 `list_files`

### 目标

列出指定目录下的文件和子目录。

### 输入示例

    {
      "path": "src"
    }

### 需要考虑

- 路径不存在
- 路径是文件而不是目录
- 目录为空
- 没有权限
- 隐藏文件
- 忽略目录
- 返回结果过长
- 排序是否稳定
- 是否递归

当前建议默认只列一层。

递归行为应由明确参数控制或暂时不支持。

### 输出建议

返回稳定、易读的文本，例如：

    src/mini_agent/
    src/mini_agent/main.py
    src/mini_agent/config.py

不要返回平台相关且难以测试的随机顺序。

---

## 2.3 `read_file`

### 目标

读取项目内一个允许访问的文本文件。

### 输入示例

    {
      "path": "src/mini_agent/main.py"
    }

### 需要考虑

- 文件不存在
- 路径是目录
- 文件过大
- 二进制文件
- 编码错误
- 文件为空
- 敏感文件
- 行数过多
- 符号链接
- 路径逃逸

当前阶段建议限制：

- 最大字节数
- 最大输出字符数或行数
- 只读取文本内容
- 拒绝敏感文件名
- 拒绝 Workspace Root 外部路径

是否支持指定行范围，可以根据实现复杂度决定。

不要在本任务中实现完整代码分页系统。

---

## 2.4 `search_text`

### 目标

在工作目录下搜索文本，并返回匹配文件和行号。

### 输入示例

    {
      "query": "LLMClient",
      "path": "src"
    }

### 需要考虑

- 查询字符串为空
- 搜索目录不存在
- 搜索路径是文件
- 大量文件
- 二进制文件
- 无权限文件
- 匹配结果过多
- 大小写敏感
- Unicode
- 被忽略的目录

当前建议：

- 只搜索普通文本文件
- 设置最大匹配数
- 返回文件相对路径和行号
- 保持结果顺序稳定
- 忽略 `.git`、虚拟环境和缓存目录

可以先使用 Python 标准库实现。

本周不要求调用系统 `grep` 或 `ripgrep`。

## 安全原则

模型提出的工具调用不能被默认信任。

以下情况必须被拒绝或限制：

    ../../.ssh/id_rsa
    /etc/passwd
    C:\Users\...\secrets.txt
    .env
    symlink-to-outside/private.txt

需要特别考虑：

- `Path.resolve()`
- 相对路径正规化
- 工作目录包含关系判断
- 符号链接逃逸

不要只检查字符串中是否包含 `..`，因为这不是可靠的安全边界。

## 验收条件

- 三个工具可以独立运行
- 三个工具均限制在 Workspace Root 内
- 非法路径被拒绝
- 敏感文件被拒绝
- 输出大小有上限
- 返回结果顺序稳定
- 错误被转换为 Tool 层错误
- 工具不依赖 Agent Loop
- 工具测试使用临时目录，不读取真实个人文件
- `pytest`、`ruff` 和 `mypy` 通过

## 测试场景

### `list_files`

- 正常目录
- 空目录
- 不存在的目录
- 输入为文件
- 路径逃逸
- 稳定排序

### `read_file`

- 正常文本文件
- 空文件
- 不存在的文件
- 输入为目录
- 文件过大
- 非法编码
- 敏感文件
- 绝对路径
- `../` 路径
- 符号链接逃逸

### `search_text`

- 单文件命中
- 多文件命中
- 无匹配
- 空查询
- 最大结果限制
- Unicode 文本
- 忽略二进制文件
- 路径逃逸
- 忽略缓存和虚拟环境目录

## 本任务暂时不做

- 写文件
- 修改文件
- 删除文件
- Shell
- Git 操作
- 网络搜索
- 正则表达式高级搜索
- AST 代码搜索
- Embedding 搜索
- 权限确认 UI

## 建议 Commit

可以根据实际工作拆分：

    feat: add workspace path safety
    feat: implement read-only file tools
    test: cover file tool security boundaries

不要为了匹配列表创建无意义 Commit。

---

# Task 3：接入模型 Tool Calling

状态：未开始

## 目标

让 LLM Client 支持：

- 将注册工具暴露给模型
- 解析模型返回的 Tool Call
- 将工具执行结果作为正确消息发送回模型

本任务只建立模型 API 与内部 Tool System 的适配边界，不实现 Agent Loop 的完整控制流程。

## 需要解决的问题

不同模型供应商可能使用不同字段表达：

- 工具定义
- Tool Call ID
- 工具名称
- 参数 JSON
- Tool Result Message
- Finish Reason

如果 Agent Loop 直接操作供应商原始 JSON：

- 核心逻辑会与 DeepSeek API 强耦合
- Mock 测试复杂
- 更换供应商需要重写 Agent
- 参数解析错误散落在多个模块

因此需要一个明确的转换边界。

## 推荐设计

### 从内部 Tool 到 API Tool Schema

将：

- name
- description
- parameter schema

转换为当前模型 API 所需格式。

转换逻辑应放在 LLM 层或供应商 Adapter 中，而不是具体工具里。

### 从 API Tool Call 到内部 ToolCall

解析：

- Tool Call ID
- 工具名称
- 参数字符串或对象

需要处理：

- 参数不是合法 JSON
- 缺少 Tool Call ID
- 缺少工具名
- 参数为空
- 一次返回多个 Tool Call
- 返回文本和 Tool Call 混合
- Finish Reason 不符合预期

当前模型 API 的具体字段必须根据实际官方文档和真实响应确认。

不要凭记忆硬编码。

### Tool Result Message

工具执行完成后，需要使用 API 要求的角色和 Tool Call ID 将结果发回模型。

项目内部 Message 模型可能需要在本任务中扩展：

- `tool` role
- Tool Call 信息
- Tool Call ID

只增加当前 Tool Calling 确实需要的字段。

不要提前设计完整多模态消息系统。

## 是否支持并行 Tool Calls

如果模型一次返回多个 Tool Call，本周可以选择：

### 方案 A：只支持一个 Tool Call

优点：

- 实现简单
- 更容易理解循环

缺点：

- 与部分模型能力不完全一致

### 方案 B：支持多个 Tool Call，但顺序执行

优点：

- 能处理多个调用
- 不引入并发复杂度

缺点：

- 模型调用语义需要明确

当前不建议直接实现并行工具执行。

开始实现前应根据真实 API 行为选择并记录。

## 验收条件

- 注册工具可以转换为模型 API Schema
- 模型 Tool Call 可以转换为内部 `ToolCall`
- 非法参数 JSON 有明确错误
- Tool Result 可以正确回传模型
- Agent 层不直接处理供应商原始 JSON
- 纯文本响应仍能正常工作
- 现有 Week 02 测试不被破坏
- `pytest`、`ruff` 和 `mypy` 通过

## 测试场景

- 模型返回纯文本
- 模型返回一个合法 Tool Call
- 工具参数为合法 JSON
- 参数为空对象
- 参数不是合法 JSON
- 工具名缺失
- Tool Call ID 缺失
- Tool Call 指向不存在的工具
- Tool Result Message 正确关联 Tool Call ID
- 多个 Tool Call 按当前设计处理
- API 返回未知字段时不会导致无关崩溃

## 本任务暂时不做

- Agent Loop
- 工具真正执行编排
- 并发 Tool Call
- 流式 Tool Call 增量拼接
- MCP
- 多供应商统一 Tool Calling
- 自动修复无效参数

## 建议 Commit

    feat: support llm tool calling contracts

---

# Task 4：实现最小 Agent Loop

状态：未开始

## 目标

实现一个最小、可预测的 Agent Loop：

    1. 接收用户任务
    2. 构造初始消息
    3. 调用模型
    4. 如果模型返回最终文本，则结束
    5. 如果模型请求工具，则执行工具
    6. 将工具结果返回模型
    7. 重复以上过程
    8. 达到最大步骤后停止

## 推荐核心行为

伪代码：

    messages = initial_messages

    for step in range(max_steps):
        response = await llm.complete(
            messages=messages,
            tools=registry.list_tools(),
        )

        if response.is_final_answer:
            return final_result

        if response.has_tool_calls:
            for tool_call in response.tool_calls:
                tool_result = await registry.execute(tool_call)
                messages.append(tool_result_message(tool_result))

            continue

        raise InvalidModelResponseError(...)

    raise MaxAgentStepsExceededError(...)

这只是行为表达，不代表最终代码结构。

## Agent Loop 应负责

- 调用模型
- 保存当前运行的消息
- 判断响应类型
- 请求 Registry 执行工具
- 将结果追加回消息
- 控制步骤数量
- 生成最终运行结果

## Agent Loop 不应负责

- 直接打开文件
- 自己实现路径安全
- 自己解析供应商原始 JSON
- 自己进行 HTTP 请求
- 读取 `.env`
- 构造复杂 UI 输出
- 保存长期会话
- 自动规划复杂任务

## 最大步骤限制

必须配置：

    MAX_AGENT_STEPS

目的：

- 防止模型无限调用工具
- 控制 Token 成本
- 控制响应时间
- 提供可预测的失败行为

达到最大步骤时，不应静默返回不完整答案。

应明确说明：

- 已达到运行上限
- 已完成多少步骤
- 最后一次模型行为是什么

## 工具执行失败

需要确定工具失败后如何处理。

推荐区分：

### 可反馈给模型的工具错误

例如：

- 文件不存在
- 搜索没有匹配
- 参数不合法
- 路径被拒绝

可以把受控错误结果返回模型，让它重新选择。

### 应终止运行的系统错误

例如：

- Registry 内部状态损坏
- 无法初始化依赖
- 不变量被破坏
- 意外的程序 Bug

不应把所有异常都伪装为普通工具输出。

## 模型请求不存在的工具

可以选择：

- 将明确错误返回模型，让模型修正
- 立即终止 Agent

当前建议将受控错误返回模型，但必须受最大步骤限制。

## 模型重复调用同一个工具

本周至少应通过最大步骤限制防止无限循环。

可以记录重复调用，但复杂重复检测可以推迟到 Week 04。

不要本周实现完整循环检测算法。

## Agent 运行结果

建议定义明确的结果对象，至少表达：

- 最终文本
- 使用步骤数
- 是否成功
- 终止原因

详细 Trace、Token 聚合和评测统计属于 Week 04。

## 日志要求

可以记录：

- 当前 Agent Step
- 模型是否请求工具
- 工具名称
- 工具是否成功
- 最终终止原因
- 总步骤数

不要默认记录：

- API Key
- 完整敏感文件内容
- 完整 Prompt
- 完整工具输出
- 用户私人数据

## 验收条件

- 纯文本任务能直接完成
- 模型调用一个工具后能回答
- 模型连续调用多个工具后能回答
- 不存在的工具有可控行为
- 工具参数错误有可控行为
- 工具失败不会让循环进入未知状态
- 达到最大步骤后明确终止
- Agent Loop 不依赖具体文件工具实现
- Agent Loop 可以使用 Mock LLM 测试
- 自动化测试不访问真实 API
- `pytest`、`ruff` 和 `mypy` 通过

## 测试场景

### 最终回答路径

- 第一次模型调用直接返回文本
- 最终文本为空
- 模型返回既无文本也无 Tool Call

### 单工具路径

- 模型请求 `list_files`
- 工具成功
- 第二次模型调用返回最终答案

### 多工具路径

- 先 `list_files`
- 再 `read_file`
- 最后返回答案

### 失败路径

- 工具不存在
- 参数格式错误
- 文件不存在
- 工具执行抛出受控异常
- 模型调用次数达到最大限制
- LLM Client 抛出网络异常
- Agent 运行被取消

### 状态验证

- 消息顺序正确
- Tool Call ID 正确关联
- 工具结果只追加一次
- 步骤计数正确
- 达到上限时没有多余模型调用

## 本任务暂时不做

- Planning
- Todo List
- Memory
- Context Compression
- Multi-Agent
- Subagent
- MCP
- 并行工具执行
- Shell
- 自动用户确认
- 完整 Trace
- Token 成本统计
- Agent Evaluation

## 建议 Commit

    feat: implement minimal agent loop

---

# Task 5：集成测试、Smoke Test、文档与周末 Review

状态：未开始

## 目标

把 Tool System 和 Agent Loop 从“能够运行”整理为“可以被团队理解、测试和继续扩展”的工程模块。

## 自动化测试要求

自动化测试必须使用：

- 临时目录
- Mock LLM Client
- Fake Tool 或测试工具
- 可预测的模型响应序列

自动化测试不得：

- 读取真实个人目录
- 访问真实模型 API
- 使用真实 API Key
- 修改开发者文件
- 依赖联网
- 依赖当前机器的绝对路径

## 推荐测试层级

### Tool 单元测试

验证：

- 参数
- 正常输出
- 安全边界
- 错误映射

### Registry 单元测试

验证：

- 注册
- 查找
- 重名
- 不存在工具

### Agent Loop 单元测试

使用 Fake LLM 和 Fake Tool，验证：

- 循环控制
- 消息追加
- 最大步骤
- 错误路径

### 最小集成测试

使用：

- 真实 Tool Registry
- 临时文件目录
- Fake LLM

验证完整链路：

    Fake LLM Tool Call
        ↓
    Registry
        ↓
    Read File Tool
        ↓
    Tool Result Message
        ↓
    Fake LLM Final Answer

## 手动 Smoke Test

允许使用真实模型完成一个受控任务，例如：

    请查看当前项目中的 Python 文件，并判断程序入口在哪里。

预期行为：

1. 模型请求 `list_files`
2. 程序执行工具
3. 模型可能请求 `read_file`
4. 程序执行工具
5. 模型给出基于真实内容的回答

Smoke Test 应确保：

- Workspace Root 指向当前仓库
- 工具只读
- `.env` 无法读取
- 不会执行 Shell
- 有最大步骤限制
- 可以通过 `Ctrl+C` 退出

## README 更新

README 至少应说明：

- 当前 Agent Harness 支持什么
- Tool System 的职责
- 当前内置工具
- 工作目录安全边界
- 如何运行 Agent
- 如何运行测试
- 如何执行 Smoke Test
- 当前明确不支持什么
- 当前安全限制

## 架构说明

可以增加一个简化流程图：

    User
      ↓
    Agent Loop
      ↓
    LLM Client
      ↓
    Tool Call
      ↓
    Tool Registry
      ↓
    Read-only Tool
      ↓
    Tool Result
      ↓
    Agent Loop
      ↓
    Final Answer

不要求本周使用复杂绘图工具。

Markdown 或 Mermaid 足够。

## Code Review 检查点

### 模块职责

- Agent Loop 是否包含具体文件操作
- Tool 是否直接调用模型
- LLM Client 是否执行工具
- `main.py` 是否承担过多业务逻辑
- Registry 是否承担了复杂调度职责

### 安全边界

- 路径是否经过真正的正规化和包含关系检查
- 是否只通过字符串搜索 `..`
- 符号链接能否逃离 Workspace Root
- `.env` 和敏感文件是否可能被读取
- 文件大小和输出数量是否有限制
- 错误中是否暴露绝对路径或敏感内容

### 类型与数据模型

- 是否仍大量传播无类型字典
- Tool Call ID 是否有明确表达
- ToolResult 是否区分成功和失败
- AgentResult 是否清晰表达终止原因
- API 专有结构是否泄漏到 Agent 层

### 异常处理

- 是否捕获宽泛异常后继续运行
- 工具的预期错误和系统错误是否区分
- 达到最大步骤时是否明确失败
- 取消是否被错误地转换为工具失败
- 不存在工具是否有稳定行为

### 测试质量

- 文件工具测试是否使用临时目录
- 是否覆盖路径逃逸
- 是否覆盖符号链接逃逸
- Agent Loop 是否使用可预测的 Fake LLM
- 是否验证真实消息顺序
- 是否有不必要的网络依赖
- 是否只测试了 Happy Path

### 可维护性

- 新增工具是否需要修改 Agent Loop
- 新增模型供应商是否需要修改 Tool 实现
- 是否存在提前设计的插件系统
- 是否存在重复路径验证代码
- 是否出现职责过大的基类

## 最终验收命令

    pytest
    ruff check .
    ruff format --check .
    mypy src

手动 Smoke Test：

    python -m mini_agent.main

具体命令应根据当前入口实现更新。

## Week 03 完成定义

只有满足以下条件，本周才算完成：

- Tool Contract 已定义
- Tool Registry 可以注册和查找工具
- `list_files` 可以安全运行
- `read_file` 可以安全运行
- `search_text` 可以安全运行
- Workspace Root 外部路径被拒绝
- 敏感文件被拒绝
- 输出大小有明确上限
- LLM Client 可以表达 Tool Calling
- Tool Call 可以转换为内部结构
- Tool Result 可以返回模型
- 最小 Agent Loop 可以完成一次工具闭环
- Agent 受到最大步骤限制
- 自动化测试不访问真实模型 API
- 自动化测试不读取真实个人文件
- 所有质量检查通过
- 至少完成一次真实 API Smoke Test
- README 已更新
- 每个核心设计决策都可以口头解释

---

## 6. 本周明确不做

Week 03 不实现：

- 写文件工具
- 删除文件工具
- 任意 Shell 执行
- Git Commit 工具
- 浏览器自动化
- MCP
- RAG
- Vector Database
- Memory
- Context Compression
- Planning
- Todo List
- Subagent
- Multi-Agent
- 并行工具调用
- 完整 Trace 系统
- Agent Benchmark
- Token 成本统计
- 桌面 UI
- Web API
- 长期会话持久化

发现这些需求时，只记录到后续计划，不在本周临时加入。

---

## 7. 本周建议 Commit 顺序

可以根据实际工作拆分为：

    feat: define tool contracts and registry
    feat: add workspace path safety
    feat: implement read-only file tools
    feat: support llm tool calling
    feat: implement minimal agent loop
    test: add tool and agent loop coverage
    docs: document tool system and agent loop

不要为了匹配该列表强行创建 Commit。

每个 Commit 应：

- 目的单一
- 可以独立理解
- 不混入无关重构
- 在提交前通过相关测试
- Commit Message 描述实际修改

---

## 8. 本周理解检查

完成 Week 03 后，我应该能够解释：

1. 为什么 Tool Calling 不是模型直接执行工具。
2. 为什么工具参数必须被视为不可信输入。
3. 为什么 Agent Loop 不应该直接访问文件系统。
4. Tool Registry 解决了什么耦合问题。
5. 为什么不能只检查路径字符串中有没有 `..`。
6. 符号链接为什么可能造成 Workspace Root 逃逸。
7. Tool Call ID 在工具结果回传中有什么作用。
8. 为什么供应商原始 Tool Call JSON 不应传播到 Agent 层。
9. 工具预期错误和系统错误有什么区别。
10. 为什么需要最大 Agent 步骤限制。
11. 模型重复调用工具时，本周依靠什么机制防止无限循环。
12. 为什么 Agent Loop 测试应该使用 Fake LLM。
13. 单元测试和真实 Smoke Test 分别验证什么。
14. 为什么本周不应该加入 Shell 和写文件能力。
15. 新增一个工具时，理想情况下哪些模块不需要修改。

---

## 9. 本周结束时更新

完成后补充：

### 实际完成内容

- 待填写

### 与计划的差异

- 待填写

### 实际技术决策

- Tool Contract 采用：待填写
- 参数验证方案：待填写
- Workspace Root 策略：待填写
- 多 Tool Call 策略：待填写
- 工具错误处理策略：待填写
- Agent 最大步骤策略：待填写

### 实际运行的检查

- `pytest`：待填写
- `ruff check .`：待填写
- `ruff format --check .`：待填写
- `mypy src`：待填写
- 真实 API Smoke Test：待填写
- 路径安全测试：待填写

### 已知问题

- 待填写

### 下一项任务

进入 Week 04：

- Agent Execution Trace
- 固定任务集
- 基础 Evaluation
- Badcase 分析
- README 与 v0.1.0 交付