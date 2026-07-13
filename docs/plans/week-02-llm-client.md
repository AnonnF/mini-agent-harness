# Week 02：LLM Client 与流式响应

## 1. 本周目标

在第一周工程基础之上，实现一个职责清晰、可测试、可替换的 LLM Client。

本周结束时，项目应能够：

- 通过配置读取模型服务地址、模型名称和 API Key
- 构造结构化的聊天消息
- 发起非流式模型请求
- 发起流式模型请求
- 在终端实时输出流式内容
- 将网络错误转换为项目内部异常
- 正确处理超时、限流和服务端错误
- 使用 Mock 测试，不在自动化测试中真实调用模型 API
- 通过一个手动 Smoke Test 验证真实 API 调用

本周只实现“模型通信层”，暂时不实现 Tool Calling 和 Agent Loop。

---

## 2. 前置条件

开始 Week 02 前，应确认 Week 01 已经完成：

- 项目采用 `src/` layout
- 项目可以正常启动
- `pyproject.toml` 已配置
- 配置模块已经存在
- 日志模块已经存在
- 项目自定义异常已经存在
- `pytest`、`ruff` 和 `mypy` 已配置
- `.env` 不会被提交到 Git

开始前运行：

    pytest
    ruff check .
    ruff format --check .
    mypy src

如果这些命令未通过，应先修复 Week 01 的问题，不要带着基础错误进入 Week 02。

---

## 3. 本周工程边界

本周主要负责以下链路：

    用户消息
        ↓
    结构化 Message
        ↓
    LLM Client
        ↓
    HTTP 请求
        ↓
    模型服务
        ↓
    普通响应或流式事件
        ↓
    项目内部 Response / Text Chunk

LLM Client 应负责：

- 将项目内部消息转换为 API 请求
- 发送 HTTP 请求
- 解析 HTTP 响应
- 解析流式事件
- 处理网络和服务端错误
- 返回项目内部统一的数据结构
- 记录必要的请求状态与耗时日志

LLM Client 不应负责：

- 保存完整会话历史
- 决定 Agent 是否继续运行
- 执行工具
- 规划任务
- 管理长期记忆
- 直接控制复杂终端界面
- 将供应商原始响应传播到整个项目

---

## 4. 建议目录结构

最终目录可以接近：

    src/
    └── mini_agent/
        ├── config.py
        ├── exceptions.py
        ├── logger.py
        ├── main.py
        └── llm/
            ├── __init__.py
            ├── base.py
            ├── models.py
            └── deepseek_client.py

    tests/
    ├── test_config.py
    └── llm/
        ├── __init__.py
        ├── test_deepseek_client.py
        └── test_stream_parser.py

实际文件数量应根据当前代码调整。

不要仅为了和计划完全一致而创建没有内容或没有职责的文件。

---

# Task 1：定义 LLM 层的职责和数据模型

状态：未开始

## 目标

在编写网络请求前，先定义项目内部如何表达：

- 一条聊天消息
- 一次完整响应
- Token 使用信息
- 流式文本片段
- LLM Client 对外接口

## 需要解决的问题

如果整个项目直接传播 API 返回的原始字典，会产生以下问题：

- 业务层依赖特定模型供应商的字段
- 类型检查能力较弱
- 测试需要构造复杂的原始 JSON
- 更换模型供应商时需要修改大量代码
- 流式和非流式响应缺少统一边界

因此需要在项目内部定义少量、稳定的数据结构。

## 推荐设计

在 `models.py` 中定义最小数据模型，例如：

- `Message`
- `MessageRole`
- `Usage`
- `ChatResponse`
- 必要时定义 `StreamChunk`

建议消息角色至少覆盖：

- system
- user
- assistant

本周暂时不需要 tool 角色，因为 Tool Calling 属于 Week 03。

在 `base.py` 中定义 LLM Client 的最小接口，至少表达：

- 非流式请求
- 流式请求

接口只描述能力，不包含具体 DeepSeek 请求细节。

## 验收条件

- 项目内部不需要到处传递无类型的消息字典
- 数据模型有完整类型标注
- 非法角色或非法数据能够被识别
- 接口能够同时表达非流式与流式请求
- 业务层不需要知道供应商原始 JSON 结构
- `mypy src` 通过

## 测试场景

- 创建合法的 system、user 和 assistant 消息
- 非法角色被拒绝
- Response 可以表达文本内容和 Usage
- 流式接口的返回类型能够被静态检查
- 数据模型不会意外包含 API Key 等配置

## 本任务暂时不做

- HTTP 请求
- API 鉴权
- SSE 解析
- 重试
- Tool Calling
- 多供应商工厂
- 依赖注入容器
- 复杂继承体系

## 建议 Commit

    feat: define llm client contracts and models

---

# Task 2：实现非流式模型请求

状态：未开始

## 目标

实现一次完整的非流式聊天请求：

    messages
        ↓
    DeepSeek Client
        ↓
    HTTP POST
        ↓
    完整 JSON 响应
        ↓
    ChatResponse

## 需要解决的问题

模型请求属于外部 I/O，具有以下不确定性：

- 网络连接失败
- 请求超时
- API Key 错误
- 请求被限流
- 服务端异常
- 响应字段缺失
- 返回内容不是合法 JSON

这些情况不能直接以底层 HTTP 异常形式泄漏到业务层。

## 推荐实现范围

`deepseek_client.py` 负责：

- 接收 Settings 或必要配置
- 创建或接收 HTTP Client
- 构造请求 Header
- 构造请求 Body
- 发送非流式请求
- 检查状态码
- 解析响应
- 转换为 `ChatResponse`
- 将底层异常转换为项目自定义异常

请求字段、鉴权方式和响应格式必须根据实际官方文档或真实响应确认，不要凭记忆猜测。

## 异常处理

至少区分：

- 配置缺失
- 鉴权失败
- 请求限流
- 请求超时
- 网络连接失败
- 服务端错误
- 响应格式错误

不要求一开始为每种状态创建大量异常类。

可以先使用清晰的项目异常，并在错误信息中保留必要上下文。

错误信息不得包含：

- 完整 API Key
- Authorization Header
- `.env` 内容
- 敏感请求信息

## 日志要求

可以记录：

- 模型名称
- 请求开始和结束
- HTTP 状态码
- 请求耗时
- 是否成功
- Token Usage

不要默认记录：

- API Key
- 完整 Prompt
- 完整模型回答
- Authorization Header

## 验收条件

- 能通过项目内部 Message 发起请求
- 能得到结构化 `ChatResponse`
- 401、429、5xx、超时和无效 JSON 能转换为明确异常
- 网络层错误不会直接传播到上层
- 日志中不存在 API Key
- HTTP Client 的生命周期处理正确
- `pytest`、`ruff` 和 `mypy` 通过

## 测试场景

使用 Mock HTTP 响应验证：

- 正常响应
- 空消息列表
- 401 鉴权失败
- 429 请求限流
- 500 服务端错误
- 请求超时
- 网络连接失败
- 返回非法 JSON
- 响应缺少必要字段
- API Key 不出现在异常信息中

## 本任务暂时不做

- 流式输出
- 自动重试
- Tool Calling
- 会话历史管理
- CLI 美化
- 多模型路由
- 请求缓存

## 建议 Commit

    feat: implement non-streaming deepseek client

---

# Task 3：实现流式响应与 SSE 解析

状态：未开始

## 目标

实现：

    async for chunk in client.stream(messages):
        ...

调用方能够逐段收到模型输出，而不是等待完整回答结束。

## 需要理解的概念

开始实现前，应理解：

- 普通 HTTP 响应和流式 HTTP 响应的区别
- 异步迭代器
- 异步生成器
- `async for`
- SSE 基本格式
- 一次网络数据块不一定等于一条完整事件
- 一条完整事件也不一定对应一个完整词语
- 流结束标志
- 流中途断开

## 推荐模块边界

流式逻辑可以分成两部分：

### HTTP 连接层

负责：

- 建立流式请求
- 读取服务端发送的数据
- 处理连接异常
- 正确关闭连接

### 流事件解析层

负责：

- 识别有效事件
- 忽略空行或无关行
- 识别结束事件
- 解析 JSON 数据
- 提取文本增量
- 将无效事件转换为明确错误

如果解析逻辑较复杂，可以提取为独立的内部函数。

不要一开始设计通用的“任意协议解析框架”。

## 验收条件

- 调用方可以通过 `async for` 接收文本片段
- 空片段不会造成异常
- 流结束能够被正确识别
- 连接中途失败能够转换为项目异常
- 无效流事件能够被识别
- HTTP 响应能够被正确关闭
- 不会将供应商原始事件传播到业务层
- `pytest`、`ruff` 和 `mypy` 通过

## 测试场景

- 单个文本事件
- 多个文本事件
- 空文本事件
- 多行事件
- 流结束事件
- 无效 JSON
- 缺少预期字段
- 流中途断开
- 服务端在建立流前返回错误状态
- 没有任何文本就结束
- Unicode 和中文内容

## 手动验证

可以通过一个临时 Smoke Test 或入口命令验证：

    python -m mini_agent.main

输入一条简单消息，确认文本能够逐段显示。

手动验证代码不得成为难以测试的核心业务逻辑。

## 本任务暂时不做

- Markdown 渲染
- 桌面 UI
- WebSocket
- 多会话并发
- Tool Calling 流式事件
- Reasoning 内容的特殊展示
- 完整聊天界面

## 建议 Commit

    feat: support streaming llm responses

---

# Task 4：超时、错误映射与有限重试

状态：未开始

## 目标

提高模型客户端面对临时网络问题时的稳定性，同时避免隐藏真实错误。

## 需要解决的问题

并非所有错误都适合重试。

可能适合重试：

- 临时网络连接错误
- 部分超时
- 部分限流响应
- 部分服务端错误

通常不应自动重试：

- API Key 错误
- 请求参数错误
- 模型名称错误
- 响应结构长期不兼容
- 用户主动取消

## 推荐实现

实现有限重试策略：

- 明确最大重试次数
- 使用适度的退避时间
- 每次重试记录日志
- 超过上限后抛出明确异常
- 不无限重试
- 不对所有异常统一重试

当前阶段可以使用简单退避，不需要引入复杂重试框架。

引入第三方重试依赖前，需要解释：

- 标准库方案是否足够
- 新依赖解决了什么问题
- 是否值得增加复杂度

## 取消与退出

需要考虑：

- 用户按下 `Ctrl+C`
- 异步任务被取消
- 流式请求被中断

取消信号通常不应该被当作普通网络错误进行自动重试。

## 验收条件

- 可重试错误最多重试指定次数
- 不可重试错误立即失败
- 每次重试都有日志
- 日志不泄露敏感信息
- 用户取消不会触发重试循环
- 超过重试次数后有明确异常
- 流式和非流式请求的错误策略一致或差异有记录
- `pytest`、`ruff` 和 `mypy` 通过

## 测试场景

- 第一次失败、第二次成功
- 达到最大重试次数
- 401 不重试
- 400 不重试
- 429 是否重试按当前设计验证
- 500 按当前设计重试
- 超时后成功
- 用户取消不重试
- 重试日志不含 API Key
- 重试次数配置为零

## 本任务暂时不做

- 熔断器
- 分布式限流
- 请求队列
- 多节点 Failover
- 自动切换模型供应商
- 复杂自适应退避算法

## 建议 Commit

    feat: add llm request error handling and retries

---

# Task 5：测试、Smoke Test、文档与周末 Review

状态：未开始

## 目标

将“能够调用模型”整理为一个可以被团队理解、测试和继续扩展的工程模块。

## 自动化测试要求

自动化测试不得真实调用模型 API。

应通过 Mock 或测试 Transport 覆盖：

- 非流式正常响应
- 流式正常响应
- 不同状态码
- 超时
- 网络错误
- 解析失败
- 重试
- 取消
- 敏感信息保护

## 手动 Smoke Test

允许保留一个需要真实 API Key 的手动测试方式，但它必须：

- 默认不被 `pytest` 自动执行
- 不在 CI 中自动调用外部 API
- 不提交真实 API Key
- 明确标记会产生 API 调用
- 提供简单运行说明

例如：

    python -m mini_agent.main

或者：

    python scripts/smoke_test_llm.py

是否创建 `scripts/` 目录应根据实际需要决定，不要只因为计划中举例就创建。

## README 更新

README 至少应补充：

- 如何配置模型服务
- 需要哪些环境变量
- 如何运行非流式示例
- 如何运行流式示例
- 如何执行测试
- 自动化测试不会真实调用 API
- 当前支持与不支持的能力

## Code Review 检查点

### 模块职责

- LLM Client 是否只负责模型通信
- `main.py` 是否承担了过多逻辑
- 配置是否从外部注入，而不是散落读取
- 原始 API JSON 是否泄漏到业务层

### 类型与接口

- 公共函数是否有完整类型标注
- 流式接口返回类型是否清晰
- 数据模型是否承担了不必要职责
- 是否存在大量无类型字典

### 异常处理

- 是否捕获了过宽的 `Exception`
- 是否错误吞掉了异常
- 是否区分可重试和不可重试错误
- 取消信号是否被错误处理
- 错误信息是否足够明确

### 资源管理

- HTTP Client 是否正确关闭
- 流式响应中断后连接是否释放
- 是否每次请求都无意义创建昂贵资源
- 测试是否残留异步资源警告

### 安全与日志

- API Key 是否可能进入日志
- `.env` 是否被忽略
- 测试数据是否包含真实密钥
- Prompt 和回答是否被不必要地完整记录

### 测试质量

- 测试是否只验证实现细节
- 是否覆盖失败路径
- 是否真实验证了流式解析
- 是否存在测试依赖真实网络
- Mock 是否模拟了合理的 API 行为

## 最终验收命令

    pytest
    ruff check .
    ruff format --check .
    mypy src

手动 Smoke Test：

    python -m mini_agent.main

## Week 02 完成定义

只有满足以下条件，本周才算完成：

- 非流式请求可以工作
- 流式请求可以工作
- API Key 从配置读取
- 网络错误被转换为项目异常
- 超时和重试行为有测试
- 自动化测试不访问真实模型 API
- 日志不包含敏感信息
- HTTP 资源能够正确释放
- README 包含使用说明
- 所有质量检查通过
- 至少完成一次真实 API Smoke Test
- 每个核心设计决策可以口头解释

---

## 5. 本周暂时不做

Week 02 明确不实现：

- Tool Calling
- Agent Loop
- Tool Registry
- 文件读取工具
- Shell 工具
- MCP
- RAG
- Memory
- Planning
- Multi-Agent
- 数据库
- Web API
- 桌面 UI
- 多模型自动路由
- 完整聊天历史持久化

如果实现过程中发现这些需求，只记录到后续计划，不在本周临时加入。

---

## 6. 本周建议 Commit 顺序

建议根据实际工作拆分为：

    feat: define llm client contracts and models
    feat: implement non-streaming deepseek client
    feat: support streaming llm responses
    feat: add llm request error handling and retries
    test: add llm client test coverage
    docs: document llm client usage

不要为了匹配该列表强行创建空 Commit。

一个 Commit 应尽量只包含一个清晰目的。

---

## 7. 本周理解检查

完成 Week 02 后，我应该能够解释：

1. 为什么 Agent Loop 不应该直接调用 `httpx`。
2. 为什么不应该让原始 API JSON 在项目中到处传播。
3. 同步函数、异步函数和异步生成器分别解决什么问题。
4. 为什么一次网络数据块不一定是一条完整 SSE 事件。
5. 超时、连接失败和 HTTP 错误有什么区别。
6. 哪些错误适合重试，哪些错误不适合重试。
7. 为什么测试不能每次真实请求模型 API。
8. Mock 测试与真实 Smoke Test 各自解决什么问题。
9. 为什么 API Key 不能出现在日志和异常信息中。
10. 为什么本周不应该提前实现 Tool Calling。

---

## 8. 本周结束时更新

完成后补充：

### 实际完成内容

- 待填写

### 与计划的差异

- 待填写

### 实际运行的检查

- `pytest`：待填写
- `ruff check .`：待填写
- `ruff format --check .`：待填写
- `mypy src`：待填写
- 真实 API Smoke Test：待填写

### 已知问题

- 待填写

### 下一项任务

进入 Week 03：Tool System 与最小 Agent Loop。