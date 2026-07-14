# Week 01：Python 工程基础

## 1. 本周目标

建立一个能够运行、测试和持续扩展的 Python 项目基础。

本周暂时不调用 DeepSeek API，不实现 Agent Loop。

本周结束时，项目应能够：

- 以 `src/` layout 组织代码
- 通过 `pyproject.toml` 安装与声明依赖
- 从环境变量加载配置（含 `.env.example`）
- 使用统一日志与项目自定义异常
- 用 pytest / ruff / mypy 做基础质量检查
- 通过 README 完成本地安装与运行

---

## 2. 本周交付物

- Python 项目初始化
- `src/` layout
- `pyproject.toml`
- 配置管理
- 日志模块
- 自定义异常
- 配置模块测试
- 基础 README

---

## 3. 建议目录结构

最终目录可以接近：

    src/
    └── mini_agent/
        ├── __init__.py
        ├── config.py
        ├── exceptions.py
        ├── logging_config.py
        └── main.py

    tests/
    ├── __init__.py
    └── test_config.py

    .env.example
    .gitignore
    pyproject.toml
    README.md

实际文件数量应根据当前代码调整。

---

# Task 1：初始化项目

状态：已完成

对应 Commit：`090d7aa` feat: initialize mini_agent package and entry point.

落地文件：`src/mini_agent/__init__.py`、`main.py`；`tests/__init__.py`

## 目标

- 创建 `src/mini_agent/`
- 创建 `tests/`
- 创建最小入口文件
- 项目可从命令行运行

## 验收条件

- `python -m mini_agent.main` 可以运行
- 输出启动信息
- 源码可以被正确导入

## 本任务暂时不做

- CLI 框架
- Web API
- Agent 功能

## 建议 Commit

    feat: initialize mini_agent package and entry point

---

# Task 2：配置 pyproject.toml

状态：已完成

对应 Commit：`30ba2ed` build: add pyproject.toml and dev tooling configuration

落地文件：`pyproject.toml`（hatchling + pytest / ruff / mypy）；`.gitignore`

## 目标

- 定义项目信息
- 定义运行依赖
- 定义开发依赖
- 配置 pytest、ruff 和 mypy

## 验收条件

- 项目可以安装
- pytest 可以发现测试
- ruff 可以检查源码
- mypy 可以检查 src

## 建议 Commit

    build: add pyproject.toml and dev tooling configuration

---

# Task 3：配置管理

状态：已完成

对应 Commit：`0b47b16` feat: add environment-based configuration loading

落地文件：`src/mini_agent/config.py`；`.env.example`

## 目标

- 通过环境变量加载配置
- 提供 `.env.example`
- 缺失必要配置时给出明确错误

## 配置项

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`
- `REQUEST_TIMEOUT`
- `MAX_AGENT_STEPS`

## 验收条件

- 正确配置可以被读取
- 整数和浮点数可以正确转换
- 缺失 API Key 时失败
- 真实 `.env` 不进入 Git

## 建议 Commit

    feat: add environment-based configuration loading

---

# Task 4：日志与异常

状态：已完成

对应 Commit：`0b2a319` feat: add centralized logging and project exceptions

落地文件：`src/mini_agent/logging_config.py`、`exceptions.py`；`config.py` 用 `ConfigurationError` 包装校验失败

## 目标

- 建立统一日志初始化
- 定义项目基础异常
- 不记录敏感信息

## 异常类型

- `MiniAgentError`
- `ConfigurationError`
- `ModelRequestError`
- `ToolExecutionError`

## 验收条件

- 日志包含时间、等级、模块和消息
- 敏感配置不出现在日志中
- 业务模块不重复配置 logger

## 建议 Commit

    feat: add centralized logging and project exceptions

---

# Task 5：测试和周末 Review

状态：已完成

对应 Commit：`b2b6104` / `5b0fbad` test: add configuration tests and project README

落地文件：`tests/test_config.py`；`README.md`；后续补强含 `scripts/check.sh`

## 测试范围

- 正确读取配置
- 默认值生效
- 缺失必填字段
- 配置类型错误

## 最终验收命令

    pytest
    ruff check .
    ruff format --check .
    mypy src

## 建议 Commit

    test: add configuration tests and project README

---

## 4. 本周完成定义

只有以下条件全部满足，Week 1 才算完成：

- 所有验收命令通过
- README 包含安装与运行步骤
- 没有真实 API Key 被提交
- 每个核心模块职责可以清楚解释
- Git Commit 按任务拆分

---

## 5. 本周暂时不做

Week 01 明确不实现：

- DeepSeek / 任意模型 API 调用
- LLM Client
- Tool Calling
- Agent Loop
- CLI 框架或 Web API

---

## 6. 本周建议 Commit 顺序

建议根据实际工作拆分为：

    feat: initialize mini_agent package and entry point
    build: add pyproject.toml and dev tooling configuration
    feat: add environment-based configuration loading
    feat: add centralized logging and project exceptions
    test: add configuration tests and project README

不要为了匹配该列表强行创建空 Commit。

---

## 7. 本周结束时更新

### 实际完成内容

- Task 1：`src/` layout、可运行入口 `python -m mini_agent.main`
- Task 2：`pyproject.toml` 配置 hatchling、pytest、ruff、mypy；`.gitignore` 忽略 `.env` 与缓存
- Task 3：`pydantic-settings` 加载配置、`.env.example`、缺失/非法配置抛 `ConfigurationError`
- Task 4：统一 `setup_logging` / `get_logger`；四类项目异常骨架
- Task 5：`tests/test_config.py`、基础 README；质量检查命令可本地复现

相关 Commit 序列：`090d7aa` → `30ba2ed` → `0b47b16` → `0b2a319` → `b2b6104` → `5b0fbad`

### 与计划的差异

- 日志模块实际文件名为 `logging_config.py`（非 `logger.py`）
- `ModelRequestError` / `ToolExecutionError` 在 Week 01 仅预留类型，业务使用发生在后续周
- `5b0fbad` 在补测试/README 之外，还顺带扩充了 Week 02 计划与 `scripts/check.sh`
- 初始化提交曾短暂带入 `__pycache__`，已在 `30ba2ed` 清理；后续应避免把缓存打进 Git

### 实际运行的检查

- `pytest`：通过（Week 01 時点以配置测试为主；当前仓库累计已扩展 LLM 测试）
- `ruff check .`：通过
- `ruff format --check .`：通过
- `mypy src`：通过
- 真实 API 调用：本周不做（符合边界）

### 已知问题

- 无阻塞性问题；工程骨架已满足进入 Week 02 的前置条件

### 下一项任务

进入 Week 02：LLM Client 与流式响应。
