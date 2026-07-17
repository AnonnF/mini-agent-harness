# Week 04：Tracing、Evaluation、Badcase 与 v0.1.0 发布

## 1. 本周目标

在 Week 03 已完成的 Tool System 和最小 Agent Loop 基础上，为 Mini Agent Harness 建立第一套可重复运行的观察与评测机制。

本周结束时，项目应具备：

- 结构化 Agent Execution Trace
- 每次运行的唯一 Run ID
- 模型调用、工具调用和终止原因记录
- 步骤数、耗时和 Token Usage 统计
- 一套固定的 Agent Evaluation Task Schema
- 至少 20 条固定任务
- 可批量执行任务的 Evaluation Runner
- 基础自动评分机制
- 汇总成功率、步骤数、耗时和 Token 的报告
- 至少 3 个 Badcase 分析
- 至少一次受控的改进前后对照实验
- 完整 README、架构说明和运行说明
- 可运行 Demo
- 发布 `v0.1.0`

本周的核心不是追求高成功率，而是建立以下闭环：

    Agent 执行
        ↓
    生成 Trace
        ↓
    固定任务评测
        ↓
    收集结果
        ↓
    分析 Badcase
        ↓
    提出一个修改
        ↓
    使用相同任务重新评测
        ↓
    比较修改前后差异

---

## 2. 前置条件

开始 Week 04 前，应确认 Week 03 已基本完成：

- Tool Contract 已定义
- Tool Registry 可以注册和查找工具
- `list_files` 可以运行
- `read_file` 可以运行
- `search_text` 可以运行
- Workspace Root 外部路径会被拒绝
- 敏感文件无法读取
- LLM Client 支持 Tool Calling
- Tool Call 可以转换为项目内部数据结构
- Tool Result 可以正确回传模型
- 最小 Agent Loop 可以完成工具调用闭环
- 最大 Agent Step 限制已经生效
- Agent Loop 可以使用 Fake LLM 测试
- 自动化测试不访问真实模型 API
- 自动化测试不读取个人真实文件

开始前运行：

    pytest
    ruff check .
    ruff format --check .
    mypy src

如果存在失败，应先判断：

- 是否属于 Week 03 未完成问题
- 是否会影响 Trace 和 Evaluation 的正确性
- 是否应该先修复再进入 Week 04

不要在 Agent Loop 基础不稳定时同时开发复杂评测系统。

---

## 3. 本周工程边界

本周主要增加三个模块。

### Tracing

负责记录一次 Agent Run 中发生了什么：

- 任务是什么
- 模型被调用了几次
- 模型请求了哪些工具
- 工具执行是否成功
- 每一步耗时
- Token Usage
- 最终如何终止
- 是否返回最终答案

Tracing 不负责判断任务是否完成得好。

### Evaluation

负责判断一次 Agent Run 是否满足任务预期：

- 是否成功结束
- 是否调用了预期工具
- 是否调用了禁止工具
- 是否包含预期关键词
- 是否超过最大步骤
- 是否发生安全违规
- 是否出现异常

Evaluation 不应改变 Agent 的运行逻辑。

### Badcase Analysis

负责解释：

- 失败发生在哪里
- 属于模型问题还是 Harness 问题
- 可能原因是什么
- 可以修改什么
- 修改是否真的改善结果
- 是否带来了新的回归问题

Badcase Analysis 不只是记录“模型答错了”。

---

## 4. 需要区分的三个概念

### Logging

用于开发和运行时排查，例如：

    INFO Agent step started
    ERROR Tool execution failed

特点：

- 主要面向开发者
- 可能是非结构化文本
- 不一定完整表达一次 Agent Run
- 常用于即时排错

### Tracing

用于重建一次完整运行过程，例如：

    Run
    ├── Model Call
    ├── Tool Call
    ├── Tool Result
    ├── Model Call
    └── Final Answer

特点：

- 具有 Run ID
- 具有明确步骤顺序
- 结构化
- 能够保存和分析

### Evaluation

用于对运行结果评分，例如：

    success = true
    expected_tools_passed = true
    keyword_score = 1.0
    step_limit_passed = true

特点：

- 输入通常是 Task + Trace + Agent Result
- 输出是评分或判定
- 用于比较不同版本

不要把日志、Trace 和 Evaluation 混成一个模块。

---

## 5. 建议目录结构

本周结束后的结构可以接近：

    src/
    └── mini_agent/
        ├── agent/
        │   ├── loop.py
        │   └── models.py
        │
        ├── evaluation/
        │   ├── __init__.py
        │   ├── models.py
        │   ├── runner.py
        │   ├── scorers.py
        │   └── report.py
        │
        ├── tracing/
        │   ├── __init__.py
        │   ├── models.py
        │   ├── recorder.py
        │   └── serialization.py
        │
        ├── llm/
        ├── tools/
        ├── config.py
        ├── exceptions.py
        ├── logger.py
        └── main.py

    evals/
    ├── tasks/
    │   └── repository_tasks.json
    ├── fixtures/
    │   └── sample_repository/
    └── results/
        └── .gitkeep

    tests/
    ├── evaluation/
    ├── tracing/
    ├── agent/
    └── ...

    docs/
    ├── architecture/
    │   └── agent-execution-flow.md
    ├── evaluations/
    │   ├── evaluation-methodology.md
    │   └── badcases.md
    └── plans/
        └── week-04-tracing-evaluation.md

实际结构应根据现有代码调整。

不要仅为了匹配计划而创建空文件或过多模块。

---

# Task 1：定义 Execution Trace 数据模型

状态：未开始

## 目标

定义一次 Agent Run 应记录哪些结构化信息，使运行过程可以被保存、查看和用于后续评测。

## 需要解决的问题

如果当前 Agent 只输出日志：

    Step 1: list_files
    Step 2: read_file
    Done

会出现以下问题：

- 无法稳定关联同一次运行
- 无法自动统计步骤
- 无法计算工具成功率
- 无法重建消息和工具执行顺序
- 无法批量比较不同版本
- 无法作为 Evaluation 输入
- 日志格式改变后分析代码容易失效

因此需要独立的结构化 Trace。

## 推荐最小模型

可以考虑定义：

- `AgentTrace`
- `TraceEvent`
- `TraceEventType`
- `TerminationReason`

### AgentTrace

至少包含：

- `run_id`
- `task_id`，可选
- `input_text`
- `started_at`
- `finished_at`
- `duration_ms`
- `events`
- `final_output`
- `success`
- `termination_reason`
- `total_steps`
- `model_call_count`
- `tool_call_count`
- `usage`，如果当前 LLM Client 能提供

### TraceEvent

至少表达：

- 事件序号
- Agent Step
- 事件类型
- 开始时间
- 结束时间或耗时
- 是否成功
- 简要元数据

事件类型可以包括：

- `model_request`
- `model_response`
- `tool_call`
- `tool_result`
- `agent_completed`
- `agent_failed`

当前不需要为每个事件创建复杂继承类。

### TerminationReason

至少区分：

- 正常返回最终答案
- 达到最大步骤
- 模型响应无效
- LLM Client 失败
- 工具系统发生不可恢复错误
- 用户取消
- 未知内部错误

## 隐私与安全要求

Trace 默认不应无条件保存：

- API Key
- Authorization Header
- `.env` 内容
- 完整敏感文件内容
- 用户私人目录绝对路径
- 完整请求 Header
- 未脱敏的凭据

对于工具输出，应考虑：

- 是否只保存摘要
- 是否截断
- 是否记录字符数而不保存全文
- 是否需要单独配置 Debug 模式

本周至少应有明确的输出长度限制。

## Trace 与 Agent Loop 的关系

Agent Loop 应在关键节点产生 Trace Event，但不应负责：

- JSON 文件写入细节
- 报告生成
- 评分
- Badcase 分类

建议通过一个简单 Recorder 或 Callback 边界接收事件。

不要在本周建立完整事件总线或可观测性平台。

## 验收条件

- 每次 Agent Run 都有唯一 Run ID
- Trace Event 顺序稳定
- Trace 可以表达成功与失败运行
- Trace 可以表达不同终止原因
- 模型调用和工具调用可被区分
- 工具成功与失败可被区分
- Trace 不泄露 API Key
- Trace 输出有长度限制
- Trace 数据模型有完整类型标注
- Trace 可以序列化为 JSON
- 现有 Agent 行为没有因 Tracing 改变
- `pytest`、`ruff` 和 `mypy` 通过

## 测试场景

- 直接返回最终答案
- 调用一个工具后完成
- 连续调用多个工具后完成
- 工具失败后模型恢复
- 达到最大步骤
- LLM Client 抛出异常
- Agent 被取消
- Trace Event 顺序正确
- Run ID 唯一
- Duration 不为负数
- 敏感字段不会被序列化
- 过长工具输出被截断
- Trace JSON 可以重新读取

## 本任务暂时不做

- Evaluation
- 图形化 Trace Viewer
- OpenTelemetry
- 分布式 Trace
- 数据库持久化
- Web Dashboard
- Prompt 全量存储
- 完整消息回放
- Token 成本换算

## 建议 Commit

    feat: add structured agent execution tracing

---

# Task 2：设计固定 Evaluation Task Schema

状态：未开始

## 目标

定义一条可重复运行的 Agent Evaluation Task 应包含哪些信息，并建立首批固定任务。

## 需要解决的问题

仅凭手动输入：

    帮我找入口文件

无法稳定评测，因为：

- 测试环境可能变化
- 预期结果没有明确记录
- 不知道应该调用哪些工具
- 不知道什么算成功
- 不同运行之间难以比较
- 修改 Prompt 后容易挑选有利案例

因此需要固定 Task Dataset。

## 推荐 Task 字段

一条 Task 可以包含：

- `id`
- `name`
- `category`
- `difficulty`
- `prompt`
- `workspace_fixture`
- `expected_tools`
- `forbidden_tools`
- `expected_keywords`
- `max_steps`
- `timeout_seconds`
- `notes`

并非所有字段都必须必填。

当前不要创建复杂 DSL。

## 推荐任务分类

首批至少包含 20 条任务。

### A. 目录与文件定位：5 条

例如：

- 列出 `src` 下的 Python 文件
- 找到程序入口文件
- 找到配置模块
- 找到自定义异常定义
- 找到 LLM Client 实现位置

### B. 代码理解：5 条

例如：

- 解释配置模块的职责
- 找到某个类的调用位置
- 总结 Agent Loop 的终止条件
- 说明 Tool Registry 的作用
- 判断某个模块依赖了哪些内部模块

### C. 多工具任务：4 条

例如：

- 先查找文件，再读取并总结
- 查找类定义，再读取调用位置
- 找到入口文件并说明启动流程
- 找到异常类并说明哪些模块使用它

### D. 失败与边界任务：3 条

例如：

- 查找不存在的函数
- 读取不存在的文件
- 搜索没有匹配的字符串

### E. 安全任务：3 条

例如：

- 请求读取 `.env`
- 请求访问 Workspace Root 外部路径
- 请求读取符号链接指向的外部敏感文件

## Fixture 原则

Evaluation 不应依赖当前仓库随时变化的真实结构。

建议准备一个小型固定 Sample Repository：

    evals/fixtures/sample_repository/

它可以包含：

- 少量 Python 文件
- 明确入口
- 配置文件
- 自定义异常
- 一个简单 Tool Registry
- 一个不存在的目标
- 一个受保护文件名
- 用于路径安全测试的结构

Fixture 应：

- 足够小
- 可预测
- 可提交到 Git
- 不含真实密钥
- 不依赖联网
- 不依赖个人绝对路径

## 验收条件

- Task Schema 有完整类型标注
- Task 文件可以被稳定加载
- Task ID 唯一
- Category 和 Difficulty 有明确取值
- 至少存在 20 条任务
- 任务覆盖正常、失败和安全场景
- 每条任务有明确成功条件
- Fixture 不包含敏感数据
- Evaluation Task 不直接包含 Agent 实现细节
- Task 加载失败时有明确错误
- `pytest`、`ruff` 和 `mypy` 通过

## 测试场景

- 正常加载一条 Task
- 加载全部 Task
- Task ID 重复
- 缺失 Prompt
- Difficulty 非法
- `max_steps` 非法
- Fixture 不存在
- JSON 格式无效
- Expected Tools 为空
- Forbidden Tools 与 Expected Tools 冲突
- Task 数量满足最低要求

## 本任务暂时不做

- LLM-as-a-Judge
- 人工评分页面
- 大规模 Benchmark
- 在线数据集下载
- 多语言评测
- Prompt 自动生成
- 动态创建任务
- 将当前开发仓库作为唯一 Fixture

## 建议 Commit

    feat: add fixed agent evaluation task set

---

# Task 3：实现 Evaluation Runner 与基础 Scorers

状态：未开始

## 目标

批量执行固定任务，并根据 Trace 和 Agent Result 生成结构化评测结果。

## 核心流程

    Load Tasks
        ↓
    为每条 Task 创建独立 Workspace
        ↓
    运行 Agent
        ↓
    收集 Agent Result 和 Trace
        ↓
    执行 Scorers
        ↓
    生成 Task Evaluation Result
        ↓
    汇总 Evaluation Report

## 推荐最小评分维度

### 1. Execution Success

检查：

- Agent 是否正常结束
- 是否发生未处理异常
- 是否达到最大步骤

### 2. Expected Tool Usage

检查：

- 是否使用预期工具
- 是否遗漏必要工具

注意：

预期工具不一定要求严格顺序，除非任务确实需要。

### 3. Forbidden Tool Usage

检查：

- 是否调用禁止工具
- 是否尝试访问受保护资源

### 4. Keyword Match

检查最终回答是否包含预期关键词。

这是基础启发式，不代表完整语义正确性。

### 5. Step Limit

检查：

- 总步骤是否在任务要求内
- 是否存在明显重复调用

### 6. Safety Result

检查：

- 路径逃逸是否被阻止
- 敏感文件是否被拒绝
- 被拒绝后 Agent 是否正确说明情况

## 评分形式

第一版优先使用简单、可解释的评分：

- `passed: bool`
- 每个 Scorer 独立给出结果
- 总体成功由明确规则计算

不要一开始创建复杂加权总分。

示例：

    {
      "task_id": "repo_001",
      "passed": true,
      "scores": {
        "execution_success": true,
        "expected_tools": true,
        "forbidden_tools": true,
        "keyword_match": true,
        "step_limit": true
      }
    }

## Runner 需要保证

- 每条任务相互隔离
- 一条任务失败不会中断整个评测
- 每条任务有独立 Run ID
- 可以设置整体任务数量限制
- 可以选择只运行某个 Category
- 结果顺序稳定
- 输出目录可配置
- 失败原因被记录

当前不要求并行运行任务。

顺序执行更容易排查问题。

## 报告内容

至少输出：

- 任务总数
- 通过数量
- 失败数量
- 总成功率
- 按 Category 成功率
- 按 Difficulty 成功率
- 平均 Agent Steps
- 最大 Agent Steps
- 平均运行时间
- 总模型调用次数
- 总工具调用次数
- Token Usage，当前可获得时
- 失败任务列表

输出格式可以包括：

- JSON：用于后续程序分析
- Markdown：用于 README 和人工查看

当前不需要 HTML Dashboard。

## 验收条件

- 可以一次运行全部固定任务
- 单条任务失败不会终止全部任务
- 每条任务得到结构化 Evaluation Result
- 每个 Scorer 可以独立测试
- 报告结果顺序稳定
- 报告可以保存为 JSON
- 报告可以生成 Markdown 摘要
- 可以按 Category 过滤
- 自动化测试默认使用 Fake LLM
- 自动化测试不产生真实 API 费用
- `pytest`、`ruff` 和 `mypy` 通过

## 测试场景

- 所有任务通过
- 某一任务失败
- Agent 抛出异常
- Agent 达到最大步骤
- 缺少预期工具
- 调用了禁止工具
- 关键词缺失
- 安全访问被正确拒绝
- Task Timeout
- 空任务集
- Category Filter
- 结果文件写入失败
- 多次执行报告顺序一致
- 一条失败不影响后续任务

## 本任务暂时不做

- 并行评测
- 分布式评测
- LLM-as-a-Judge
- 模糊语义评分
- Web Dashboard
- 数据库存储
- 云端 Benchmark
- 自动 Prompt 优化
- 自动修改 Agent 代码

## 建议 Commit

可以拆分为：

    feat: implement agent evaluation runner
    feat: add deterministic evaluation scorers
    feat: generate evaluation reports

---

# Task 4：Badcase 分类与一次受控改进实验

状态：未开始

## 目标

选择至少 3 条失败任务，形成结构化 Badcase 分析，并针对其中一个问题完成一次受控改进。

## Badcase 模板

每个 Badcase 至少记录：

### Task

任务 ID、任务描述和预期行为。

### Observed Behaviour

实际发生了什么。

### Trace Evidence

指出：

- 失败发生在哪一步
- 模型请求了什么
- 工具返回了什么
- Agent 如何继续
- 最终如何终止

### Failure Layer

至少区分：

- 模型能力问题
- Prompt 问题
- Tool Description 问题
- Tool 参数 Schema 问题
- Tool 实现问题
- Agent Loop 控制问题
- Evaluation 规则问题
- Fixture 或测试数据问题

### Root Cause Hypothesis

说明可能原因。

这里是“假设”，不要伪装成已经证明的事实。

### Proposed Change

只提出一个范围明确的修改。

### Regression Risk

说明修改可能造成的副作用。

### Verification

使用同一套 Task 重新评测，并比较结果。

## 推荐第一批 Badcase 类型

### 重复工具调用

例如：

- 模型连续调用相同 `list_files`
- 没有利用上一轮 Tool Result

### 工具选择错误

例如：

- 应使用 `search_text`，却多次读取无关文件
- 应先列目录，却直接猜测文件路径

### 输出正确但评分失败

例如：

- 答案语义正确，但没有命中固定关键词
- 暴露了 Evaluation 规则过于僵硬

### 安全拒绝后表达不清

例如：

- 工具正确拒绝 `.env`
- 但 Agent 最终声称文件不存在，而不是说明访问被禁止

## 受控实验要求

只选择一个修改变量，例如：

- 调整 System Prompt
- 改善某个 Tool Description
- 调整 Tool 参数说明
- 修复 Agent Loop 的消息追加问题
- 修复 Evaluation Keyword 规则

不要同时修改多个变量，否则无法判断是什么带来了变化。

记录：

    Baseline Version
    Baseline Report
    Proposed Change
    Updated Version
    Updated Report
    Improvement
    Regression
    Conclusion

## Ablation 思维

本周不要求正式学术级 Ablation，但至少做到：

- 修改前运行固定任务
- 只修改一个主要因素
- 修改后运行相同任务
- 比较相同指标
- 检查是否出现新的失败

模型评测、Agent 系统评测和最终产品评测需要明确区分；随机采样也会影响回归结果，因此本周的自动评测应尽量使用稳定参数或 Fake LLM。:contentReference[oaicite:1]{index=1}

## 验收条件

- 至少分析 3 个 Badcase
- 每个 Badcase 引用真实 Trace
- 每个 Badcase 有失败层分类
- 推测和事实被区分
- 至少选择一个 Badcase 做修改
- 修改前后使用相同任务集
- 修改前后报告被保存
- 能说明成功率是否提升
- 能说明是否产生回归
- 如果没有提升，也如实记录
- 不为了提高分数修改测试答案
- `pytest`、`ruff` 和 `mypy` 通过

## 本任务暂时不做

- 自动修复 Agent
- 自动 Prompt 搜索
- 多模型大规模对比
- 人工偏好数据收集
- LLM-as-a-Judge
- 复杂统计显著性检验
- 修改多项变量后声称单一原因有效

## 建议 Commit

根据实际修改决定，例如：

    docs: document initial agent badcases
    fix: improve read file tool description
    test: add regression case for repeated tool calls

---

# Task 5：README、架构文档、Demo 与 v0.1.0

状态：未开始

## 目标

将前四周成果整理为一个可以被其他开发者安装、理解、运行和评测的首个版本。

## README 最低内容

### Project Overview

说明：

- Mini Agent Harness 是什么
- 解决什么问题
- 当前项目学习目标
- 为什么不直接使用 LangChain 或 LangGraph

### Features

列出当前真实支持：

- DeepSeek LLM Client
- 非流式和流式响应
- Tool Calling
- Tool Registry
- 只读文件工具
- Workspace Root 安全边界
- 最小 Agent Loop
- 最大步骤限制
- Execution Trace
- Fixed Evaluation Tasks
- Evaluation Report

不要列出未完成能力。

### Architecture

展示：

    User
      ↓
    Agent Loop
      ↓
    LLM Client
      ↓
    Model Response
      ├── Final Answer
      └── Tool Call
            ↓
         Tool Registry
            ↓
         Read-only Tool
            ↓
         Tool Result
            ↓
         Agent Loop

Tracing 横向观察整个流程：

    Agent Loop ──────→ Trace Recorder
    Tool Registry ───→ Trace Recorder
    LLM Client ──────→ Trace Recorder

Evaluation 使用：

    Task + Agent Result + Trace
                ↓
            Scorers
                ↓
         Evaluation Report

### Quick Start

至少包括：

- Python 版本
- 克隆仓库
- 创建环境
- 安装依赖
- 创建 `.env`
- 启动项目
- 运行测试
- 运行评测

### Configuration

列出环境变量名称及用途，但不包含真实值。

### Safety Boundaries

明确说明：

- 工具只读
- 只能访问 Workspace Root
- `.env` 被拒绝
- 不支持 Shell
- 不支持写文件
- 不支持网络浏览
- 输出有大小限制
- Agent 有最大步骤限制

### Evaluation

说明：

- Task 数量
- Task 分类
- 评分方式
- 当前成功率
- 评测限制
- Fake LLM 与真实模型测试的区别

### Known Limitations

例如：

- 仅支持一个模型供应商
- 语义评分较简单
- 没有长期记忆
- 没有 Context Compression
- 没有 MCP
- 没有复杂 Planning
- 没有 Shell
- 没有并行 Tool Calls

### Roadmap

只列后续方向，不暗示已经完成。

## 架构文档

建议增加：

    docs/architecture/agent-execution-flow.md

记录：

- 各模块职责
- 依赖方向
- 一次 Agent Run 的时序
- Tool Calling 数据转换边界
- Trace 数据流
- Evaluation 数据流
- 安全边界
- 已知限制

## Evaluation 文档

建议增加：

    docs/evaluations/evaluation-methodology.md
    docs/evaluations/badcases.md

### evaluation-methodology.md

记录：

- 为什么选择固定任务
- Task Schema
- Fixture 设计
- Scorer 定义
- 总体 Passed 规则
- 当前评测局限
- 如何复现结果

### badcases.md

记录至少三个真实失败案例。

## Demo

录制一个 2～4 分钟 Demo。

建议流程：

1. 简要展示项目结构
2. 启动 Agent
3. 输入一个需要多工具的任务
4. 展示模型 Tool Call
5. 展示工具执行
6. 展示最终回答
7. 展示对应 Trace
8. 运行 Evaluation
9. 展示报告
10. 简要说明一个 Badcase

不要只展示完全成功的聊天回答。

## 发布前检查

### 代码质量

    pytest
    ruff check .
    ruff format --check .
    mypy src

### 安全检查

确认没有提交：

- `.env`
- API Key
- Token
- 密码
- 个人绝对路径
- 真实私人文件
- 测试运行产生的大量结果
- 虚拟环境
- 缓存

### Git 检查

    git status
    git diff
    git log --oneline

### 安装验证

最好在一个干净环境中验证：

- 项目可以安装
- 项目可以启动
- 测试可以运行
- Evaluation 可以运行

### Tag

确认完成后：

    git tag v0.1.0
    git push origin v0.1.0

是否创建 GitHub Release 可以根据仓库状态决定。

## v0.1.0 完成定义

只有满足以下条件才发布：

- 项目可以正常安装
- LLM Client 可以工作
- 流式响应可以工作
- Tool Calling 可以工作
- 三个只读工具可以工作
- Workspace Root 安全边界已测试
- 最小 Agent Loop 可以完成真实任务
- 最大步骤限制已测试
- Trace 可以保存
- 20 条固定任务存在
- Evaluation Runner 可以执行
- 报告可以生成
- 至少完成 3 个 Badcase 分析
- 至少完成一次修改前后对照实验
- README 完整
- 架构文档完整
- 所有质量检查通过
- 至少完成一次真实模型 Smoke Test
- 没有提交敏感信息
- 已知限制被真实记录

## 建议 Commit

    docs: add agent architecture and evaluation methodology
    docs: document initial badcase analysis
    docs: prepare v0.1.0 release
    chore: release v0.1.0

不要为了匹配该列表创建空 Commit。

---

## 6. 本周明确不做

Week 04 不实现：

- Memory
- Context Compression
- Token Budget Manager
- RAG
- Vector Database
- Planning
- Todo List
- Subagent
- Multi-Agent
- MCP
- Shell
- 写文件
- Git 自动修改
- 浏览器自动化
- Web Dashboard
- 数据库存储 Trace
- OpenTelemetry
- 分布式 Evaluation
- LLM-as-a-Judge
- 自动 Prompt 优化
- 多供应商模型对比
- 云端部署

本周目标是完成第一个可评测版本，而不是开始第二阶段。

---

## 7. 本周建议 Commit 顺序

可以根据实际开发拆分为：

    feat: add structured agent execution tracing
    feat: add fixed agent evaluation task set
    feat: implement agent evaluation runner
    feat: add deterministic evaluation scorers
    feat: generate evaluation reports
    docs: document agent badcases
    docs: add architecture and evaluation guides
    docs: prepare v0.1.0 release
    chore: release v0.1.0

每个 Commit 应：

- 只包含一个清晰目的
- 不混入无关重构
- 在提交前通过相关测试
- 能够独立理解
- Message 与实际修改一致

---

## 8. 本周理解检查

完成 Week 04 后，我应该能够解释：

1. Logging、Tracing 和 Evaluation 有什么区别。
2. 为什么一次 Agent Run 需要 Run ID。
3. Trace 应该记录什么，不应该记录什么。
4. 为什么 Trace 不应默认保存完整敏感工具输出。
5. Evaluation Task 为什么需要固定 Fixture。
6. 为什么不能只在当前真实仓库上做评测。
7. 为什么自动化测试应使用 Fake LLM。
8. Fake LLM 测试与真实模型评测分别验证什么。
9. Expected Tools 和最终答案正确性有什么区别。
10. 为什么关键词匹配只能作为基础启发式。
11. 为什么不应一开始使用 LLM-as-a-Judge。
12. 怎样区分模型错误、工具错误和 Agent Loop 错误。
13. 什么是 Badcase 的 Root Cause Hypothesis。
14. 为什么修改前后必须使用同一套任务。
15. 为什么一次实验最好只修改一个主要变量。
16. 成功率提高为什么不一定意味着系统整体变好。
17. 为什么还需要检查步骤数、耗时和 Token。
18. 为什么达到最大步骤属于一种明确终止原因。
19. 一个评测规则本身可能出现什么问题。
20. 为什么本周应该发布 v0.1.0，而不是继续无限增加功能。

---

## 9. 与模型学习线的同步安排

Week 04 的模型学习主题建议是：

- Embedding 的基本原理
- Token Embedding 与 Position Information
- 模型评测与 Agent 系统评测的区别
- 随机采样对回归测试的影响
- Temperature 对稳定性的影响
- Badcase 分类
- 基础 Ablation Experiment

本周模型学习产物可以是：

    llm-foundations-lab/
    └── 04-embedding/
        ├── embedding_shapes.ipynb
        ├── position_embedding.py
        └── notes.md

最低产物：

- 使用 PyTorch 创建一个 Embedding Layer
- 输入 Token ID 并观察输出 Shape
- 解释 Vocabulary Size 与 Embedding Dimension
- 比较相同 Token 在不同位置上的表示
- 写一页笔记说明模型评测与 Agent Evaluation 的区别

模型学习线每周建议保持约 4～5 小时，不应挤压 Harness 的主要工程时间。:contentReference[oaicite:2]{index=2}

---

## 10. 本周结束时更新

完成后补充：

### 实际完成内容

- 待填写

### 与计划的差异

- 待填写

### 实际技术决策

- Trace 数据模型：待填写
- Trace 保存格式：待填写
- 工具输出截断策略：待填写
- Evaluation Task Schema：待填写
- Fixture 策略：待填写
- Overall Passed 规则：待填写
- Keyword Scorer 规则：待填写
- Safety Scorer 规则：待填写

### 实际评测结果

- Task 总数：待填写
- Passed：待填写
- Failed：待填写
- Success Rate：待填写
- 平均 Steps：待填写
- 平均 Duration：待填写
- Token Usage：待填写
- Safety Tasks Passed：待填写

### Badcase

- Badcase 1：待填写
- Badcase 2：待填写
- Badcase 3：待填写

### 对照实验

- 修改内容：待填写
- Baseline：待填写
- Updated：待填写
- Improvement：待填写
- Regression：待填写
- Conclusion：待填写

### 实际运行的检查

- `pytest`：待填写
- `ruff check .`：待填写
- `ruff format --check .`：待填写
- `mypy src`：待填写
- 真实 API Smoke Test：待填写
- Evaluation Runner：待填写
- Clean Environment Installation：待填写

### 发布状态

- README：待填写
- 架构文档：待填写
- Demo：待填写
- Git Tag：待填写
- GitHub Release：待填写

### 已知问题

- 待填写

### 下一阶段

进入 Month 02：

- LLM 与 Agent 基础机制
- Token 与 Context Window
- Sampling
- KV Cache
- Agent Prompt
- 更系统的 Tool Use