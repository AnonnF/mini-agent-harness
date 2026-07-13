# Week 01：Python 工程基础

## 本周目标

建立一个能够运行、测试和持续扩展的 Python 项目基础。

本周暂时不调用 DeepSeek API，不实现 Agent Loop。

## 本周交付物

- Python 项目初始化
- `src/` layout
- `pyproject.toml`
- 配置管理
- 日志模块
- 自定义异常
- 配置模块测试
- 基础 README

## Task 1：初始化项目

状态：已完成

目标：

- 创建 `src/mini_agent/`
- 创建 `tests/`
- 创建最小入口文件
- 项目可从命令行运行

验收：

- `python -m mini_agent.main` 可以运行
- 输出启动信息
- 源码可以被正确导入

暂时不做：

- CLI 框架
- Web API
- Agent 功能

## Task 2：配置 pyproject.toml

状态：已完成

目标：

- 定义项目信息
- 定义运行依赖
- 定义开发依赖
- 配置 pytest、ruff 和 mypy

验收：

- 项目可以安装
- pytest 可以发现测试
- ruff 可以检查源码
- mypy 可以检查 src

## Task 3：配置管理

状态：已完成

目标：

- 通过环境变量加载配置
- 提供 `.env.example`
- 缺失必要配置时给出明确错误

配置项：

- DEEPSEEK_API_KEY
- DEEPSEEK_BASE_URL
- DEEPSEEK_MODEL
- REQUEST_TIMEOUT
- MAX_AGENT_STEPS

验收：

- 正确配置可以被读取
- 整数和浮点数可以正确转换
- 缺失 API Key 时失败
- 真实 `.env` 不进入 Git



## Task 4：日志与异常

状态：已完成

目标：

- 建立统一日志初始化
- 定义项目基础异常
- 不记录敏感信息

异常类型：

- MiniAgentError
- ConfigurationError
- ModelRequestError
- ToolExecutionError

验收：

- 日志包含时间、等级、模块和消息
- 敏感配置不出现在日志中
- 业务模块不重复配置 logger



## Task 5：测试和周末 Review

状态：已完成

测试范围：

- 正确读取配置
- 默认值生效
- 缺失必填字段
- 配置类型错误

最终命令：

```
pytest
ruff check .
ruff format --check .
mypy src
```



## 本周完成定义

只有以下条件全部满足，Week 1 才算完成：

- 所有验收命令通过
- README 包含安装与运行步骤
- 没有真实 API Key 被提交
- 每个核心模块职责可以清楚解释
- Git Commit 按任务拆分

