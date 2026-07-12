```markdown
# Mini Agent Harness 项目交接上下文

## 1. 项目定位

说明：

- **项目要解决什么问题**：从零实现一个可维护、可测试、可扩展的 Mini Agent Harness，用于学习和实践真实软件工程流程，而不是一次性脚本或 Demo。
- **项目的长期目标**：月底（Month 01）具备规范 Python 工程、统一配置/日志/异常、DeepSeek API 调用、最小工具系统、最小 Agent Loop、基础测试与固定评测任务、完整 README 和本地运行方法。
- **当前主要准备的岗位方向**：未记录（仓库文档与规则中未提及具体岗位方向）。
- **当前采用的开发原则**：
  - 工程化目录结构，模块职责清晰
  - 配置、日志、网络请求、工具执行、Agent 逻辑分离
  - 核心逻辑与具体模型供应商/框架解耦
  - 所有外部输入必须验证，不可靠操作必须有失败路径
  - 不硬编码 API Key、URL、超时等环境相关配置
  - 工程化不等于复杂化，避免无实际需求的抽象
- **为什么强调工程化开发**：项目目标不仅是实现功能，还要让代码具备可维护性、可扩展性、可测试性和可观测性，并能按真实团队流程迭代。
- **当前明确不使用或暂不使用的技术**：
  - LangChain、LangGraph（当前阶段不用于隐藏 Agent Loop、Tool Calling、Context Management）
  - Multi-Agent、MCP、长期记忆、RAG、向量数据库、浏览器自动化、任意 Shell 执行、完整桌面 UI、模型微调、复杂数据库、微服务拆分（Month 01 明确不做）
  - CLI 框架、Web API、Agent 功能（Week 01 Task 1 明确不做）

## 2. Cursor 协作方式

总结当前项目对 Cursor 的要求，包括：

- **Cursor 是软件工程导师和代码审查者，而不是代替开发**：优先指导需求、模块划分、接口设计、测试、实现、质量检查、Review、文档、Commit；默认由开发者亲手完成主要实现。
- **每次只处理一个小任务**：范围明确，不一次生成完整项目或多个完整模块。
- **代码前要解释设计思路、模块职责和取舍**：需说明当前问题、工程背景、模块职责边界、推荐方案、开发者需完成的部分、验证方式；区分「当前必须实现 / 未来扩展边界 / 当前不应提前实现」。
- **不要一次生成完整项目**：除非开发者明确要求，否则不直接修改文件，优先提供接口骨架、局部实现或伪代码。
- **不要擅自重构无关代码**：不未经讨论改变技术栈，不为未来可能需求提前增加复杂抽象。
- **每个功能必须包含测试和验收**：每项功能需定义验收条件；优先让开发者根据测试场景自己实现测试，不直接生成全部测试代码。
- **Code Review 时如何区分问题严重程度**：
  - **必须修改**：错误、安全问题或明显维护风险
  - **建议修改**：改善结构、测试能力或可读性
  - **可选优化**：当前不修改也不影响质量
- **回复格式尽量采用**：当前任务 / 工程背景 / 设计方案 / 实现步骤 / 最少示例 / 测试与验收 / Code Review 检查点 / 理解检查；最后提出 2–4 个理解确认问题。
- **Python 文件额外规范**（`python-quality.mdc`）：完整类型标注、有意义命名、验证外部输入、设计失败路径、I/O 与业务逻辑分离、不记录敏感信息、避免宽泛异常静默忽略、模块职责有限。

## 3. 当前阶段

写清楚：

- **当前处于第几个月**：Month 01（工程基础月）
- **当前处于第几周**：Week 01（Python 工程基础）
- **当前正在处理哪个 Task**：Task 1 和 Task 2 已完成；**下一项任务是 Task 3（配置管理）**
- **本月目标**：建立 Mini Agent Harness 工程基础（目录、配置、日志异常、DeepSeek 调用、工具系统、Agent Loop、测试、评测、README），而非完整 Agent 产品。
- **本周目标**：建立可运行、可测试、可扩展的 Python 项目基础；本周暂不调用 DeepSeek API，不实现 Agent Loop。
- **当前 Task 的目标**（已完成 Task 2；计划中的下一 Task 为 Task 3）：
  - Task 3 目标：通过环境变量加载配置；提供 `.env.example`；缺失必要配置时给出明确错误。
- **当前 Task 的验收条件**（Task 3，来自 `docs/plans/week-01-foundation.md`）：
  - 正确配置可以被读取
  - 整数和浮点数可以正确转换
  - 缺失 API Key 时失败
  - 真实 `.env` 不进入 Git

**计划文件与实际状态差异**：`docs/plans/week-01-foundation.md` 中 Task 1–5 的状态仍全部标记为「未开始」，与实际代码/Git 进度不一致；**以实际代码和 Git 为准**。

## 4. 当前 Git 状态

列出：

- **当前分支**：`main`
- **当前 HEAD commit**：`30ba2ed306a8cb05b229dd5265d081fcd0dfde80`
  - Subject：`build: add pyproject.toml and dev tooling configuration`
  - Body：`Configure hatchling src layout, pytest, ruff, and mypy so the project can be installed and checked without PYTHONPATH.`
- **工作区是否干净**：是（`nothing to commit, working tree clean`）
- **未提交修改**：无
- **未跟踪文件**：无（已跟踪文件见下方 `git ls-files` 列表）
- **是否存在尚未推送的 Commit**：是；`Your branch is ahead of 'origin/main' by 2 commits`

**完整提交历史（本地）**：

| Commit | Message |
|--------|---------|
| `e3cdd05` | `chore: add project engineering rules` |
| `b2ebbbf` | `docs: add plans for current project` |
| `090d7aa` | `feat: initialize mini_agent package and entry point.` |
| `30ba2ed` | `build: add pyproject.toml and dev tooling configuration` |

**`git diff` / `git diff --cached`**：均为空。

## 5. 当前项目目录结构

```text
mini-agent-harness/
├── .cursor/rules/
│   ├── engineering-workflow.mdc   # Cursor 协作与导师式开发流程规则
│   ├── mini-agent-core.mdc          # 项目定位、架构原则、技术约束
│   └── python-quality.mdc           # Python 工程质量、类型、测试规范
├── .gitignore                       # 忽略 .venv、__pycache__、.env、工具缓存等
├── README.md                        # 占位文件，当前为空
├── pyproject.toml                   # 项目元数据、构建、开发依赖、pytest/ruff/mypy 配置
├── docs/plans/
│   ├── month-01-roadmap.md          # 本月四周路线图与验收标准
│   └── week-01-foundation.md        # 本周 Task 1–5 细分计划
├── src/mini_agent/
│   ├── __init__.py                  # 包标识，导出 __version__
│   └── main.py                      # 命令行入口模块
└── tests/
    └── __init__.py                  # 测试包占位，尚无测试用例
```

**已跟踪文件完整列表**（`git ls-files`）：

`.cursor/rules/engineering-workflow.mdc`、`.cursor/rules/mini-agent-core.mdc`、`.cursor/rules/python-quality.mdc`、`.gitignore`、`README.md`、`docs/plans/month-01-roadmap.md`、`docs/plans/week-01-foundation.md`、`pyproject.toml`、`src/mini_agent/__init__.py`、`src/mini_agent/main.py`、`tests/__init__.py`

**本地存在但未纳入 Git 的常见目录**（被 `.gitignore` 忽略）：`.venv/`、各类缓存目录。

## 6. 已经完成的工作

按照完成顺序列出已经真实完成的工作。

### 6.1 添加 Cursor 工程规则

- **完成了什么**：建立项目级 Cursor 规则（核心原则、协作流程、Python 质量规范）。
- **文件**：`.cursor/rules/mini-agent-core.mdc`、`engineering-workflow.mdc`、`python-quality.mdc`
- **当前支持什么行为**：指导 Cursor 以导师/审查者角色协作。
- **如何验证**：文件存在于仓库。
- **是否已提交**：是（`e3cdd05`）

### 6.2 添加项目计划文档

- **完成了什么**：编写 Month 01 路线图和 Week 01 基础计划。
- **文件**：`docs/plans/month-01-roadmap.md`、`docs/plans/week-01-foundation.md`
- **当前支持什么行为**：作为开发路线和验收依据。
- **如何验证**：文件存在于仓库。
- **是否已提交**：是（`b2ebbbf`）

### 6.3 Task 1：初始化项目

- **完成了什么**：创建 `src/mini_agent/` 包、`tests/` 占位、最小入口 `main.py`。
- **文件**：`src/mini_agent/__init__.py`、`src/mini_agent/main.py`、`tests/__init__.py`
- **当前支持什么行为**：
  - 可通过 `python3 -m mini_agent.main` 启动（安装后无需 `PYTHONPATH`；安装前需 `PYTHONPATH=src`）
  - 输出启动信息
  - 包可被导入
- **如何验证**：
  - `PYTHONPATH=src python3 -m mini_agent.main`（Task 1 阶段已验证）
  - `PYTHONPATH=src python3 -c "from mini_agent.main import main; import mini_agent"`
- **是否已提交**：是（`090d7aa`）
- **备注**：该提交曾误包含 `src/mini_agent/__pycache__/main.cpython-314.pyc`，已在 Task 2 提交中删除。

### 6.4 Task 2：配置 pyproject.toml 与开发工具链

- **完成了什么**：
  - 添加 `pyproject.toml`（hatchling 构建、项目元数据、dev 依赖、pytest/ruff/mypy 配置）
  - 添加 `.gitignore`
  - 创建空 `README.md` 占位
  - 更新 `main.py` 输出带版本号的启动信息
  - 删除误提交的 `__pycache__` 文件
- **文件**：`pyproject.toml`、`.gitignore`、`README.md`、`src/mini_agent/main.py`（修改）
- **当前支持什么行为**：
  - `pip install -e ".[dev]"` 可编辑安装
  - 安装后可直接 `python3 -m mini_agent.main`
  - `pytest` 可发现 `tests/`（当前 0 个测试）
  - `ruff check .` 可检查源码
  - `mypy src` 可类型检查（开发者环境中已通过）
- **如何验证**：见第 10 节命令状态。
- **是否已提交**：是（`30ba2ed`）

## 7. 当前代码实现

说明当前已经存在的模块。

### 7.1 `src/mini_agent/__init__.py`

- **模块职责**：标识 `mini_agent` 为 Python 包；提供版本号。
- **对外接口**：`__version__`（值为 `"0.0.0"`）
- **依赖**：无
- **被依赖**：`src/mini_agent/main.py`
- **实现是否完整**：Task 1/2 范围内完整
- **已知限制**：版本号与 `pyproject.toml` 中 `version = "0.0.0"` 重复维护，尚未统一为单一来源

### 7.2 `src/mini_agent/main.py`

- **模块职责**：项目命令行入口。
- **对外接口**：`main() -> None`
- **依赖**：`mini_agent`（读取 `__version__`）
- **被依赖**：通过 `python3 -m mini_agent.main` 作为模块入口执行
- **实现是否完整**：Task 1/2 范围内完整（仅打印启动信息）
- **已知限制**：
  - 使用 `print()`，尚未接入统一日志（计划 Task 4）
  - 无配置加载（计划 Task 3）
  - 无 CLI 参数解析

### 7.3 `tests/__init__.py`

- **模块职责**：测试包占位。
- **对外接口**：无
- **依赖**：无
- **被依赖**：pytest 测试发现
- **实现是否完整**：仅占位，无实际测试
- **已知限制**：无任何测试用例（计划 Task 5 编写配置相关测试）

### 7.4 尚未实现的计划模块

以下模块在计划中但**当前不存在**：

- 配置管理模块（Task 3）
- 日志模块（Task 4）
- 自定义异常体系（Task 4）
- LLM Client（Week 2）
- Tool System / Agent Loop（Week 3）
- Tracing / Evaluation（Week 4）

## 8. 关键技术决策

### Python 版本

- **最终选择**：`requires-python = ">=3.12"`；开发者环境实测 **Python 3.14.4**
- **选择原因**：计划要求现代 Python；当前开发机使用 3.14.4
- **放弃的替代方案**：未记录
- **对后续开发的影响**：mypy 配置使用 `python_version = "3.12"` 作为检查基准，与运行版本 3.14 可能存在差异

### 包和依赖管理方式

- **最终选择**：`pyproject.toml` + **hatchling** 构建后端 + `pip install -e ".[dev]"`
- **选择原因**：符合项目工程规范；hatchling 配置较少；dev 依赖通过 `[project.optional-dependencies]` 管理
- **放弃的替代方案**：setuptools（未采用）；`[dependency-groups]` PEP 735 语法（未采用，使用的是 `optional-dependencies`）
- **对后续开发的影响**：项目名 `mini-agent-harness` 与包名 `mini_agent` 不一致，需显式配置 `[tool.hatch.build.targets.wheel] packages = ["src/mini_agent"]`

### 是否采用 `src/` layout

- **最终选择**：是
- **选择原因**：项目规则与 Month 01 计划明确要求
- **放弃的替代方案**：平铺式包目录（未采用）
- **对后续开发的影响**：测试通过 `pythonpath = ["src"]` 配置；安装后无需手动 `PYTHONPATH`

### 测试框架

- **最终选择**：pytest（`>=8.0`，实测安装 9.1.1）
- **选择原因**：项目规范要求
- **放弃的替代方案**：未记录
- **对后续开发的影响**：`testpaths = ["tests"]` 已配置，等待 Task 5 添加真实测试

### 类型检查工具

- **最终选择**：mypy（`>=1.13`，实测安装 2.2.0）
- **选择原因**：项目规范要求
- **配置**：`mypy_path = "src"`，`packages = ["mini_agent"]`，`disallow_untyped_defs = true`，`strict = false`
- **对后续开发的影响**：新增模块需保持类型标注

### 代码质量工具

- **最终选择**：ruff（`>=0.8`，实测安装 0.15.21）用于 lint 和 format
- **选择原因**：项目规范要求
- **配置**：`select = ["E", "F", "I", "UP"]`，`line-length = 88`
- **对后续开发的影响**：Week 01 最终验收要求 `ruff format --check .` 通过，当前尚未满足

### 配置管理方案

- **最终选择**：计划使用 **pydantic-settings**（Task 3），当前**未实现**
- **选择原因**：Month 01 工程原则已写明
- **放弃的替代方案**：未记录
- **对后续开发的影响**：Task 3 将把 `pydantic-settings` 加入运行依赖

### 日志方案

- **最终选择**：计划使用 Python logging 或结构化日志（Task 4），当前**未实现**
- **选择原因**：项目技术规范
- **对后续开发的影响**：`main.py` 中 `print()` 为临时方案

### 异常体系

- **最终选择**：计划定义 `MiniAgentError`、`ConfigurationError`、`ModelRequestError`、`ToolExecutionError`（Task 4），当前**未实现**

### 异步或同步策略

- **最终选择**：未记录（当前代码均为同步）

### LLM Client 的边界设计

- **最终选择**：未实现；Week 2 计划与 Agent Loop 分离
- **选择原因**：Month 01 原则要求配置、日志、模型调用、工具系统、Agent Loop 分离
- **对后续开发的影响**：Week 2 将独立实现 DeepSeek 客户端

### 是否使用 LangChain 或 LangGraph

- **最终选择**：**不使用**（当前阶段明确禁止）
- **选择原因**：避免隐藏 Agent Loop、Tool Calling、Context Management 等核心机制
- **放弃的替代方案**：LangChain / LangGraph
- **对后续开发的影响**：需自行实现 Agent Loop 和 Tool Calling

## 9. 依赖和开发环境

### 操作系统相关信息

- **已验证环境**：Linux（开发者使用 WSL2，内核 `linux 6.18.33.2-microsoft-standard-WSL2`）
- **其他平台**：Windows/macOS 命令未在本仓库验证，以下为通用 Python 项目做法

### Python 版本

- **要求**：`>=3.12`（`pyproject.toml`）
- **已验证版本**：Python 3.14.4
- **注意**：系统可能只有 `python3` 命令，无 `python` 命令（实测 `python` 不存在，需用 `python3`）

### 包管理工具

- **pip**（实测 25.1.1，位于 `.venv` 内）
- **构建后端**：hatchling

### 创建虚拟环境

**Linux / macOS：**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)：**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 安装依赖的命令

```bash
pip install -e ".[dev]"
```

- 运行依赖当前为空（`dependencies = []`）
- 开发依赖：`pytest`、`ruff`、`mypy`
- 开发者曾使用清华 PyPI 镜像（`https://pypi.tuna.tsinghua.edu.cn/simple`），此为个人环境配置，非项目要求

### 环境变量名称（计划 Task 3，当前未实现）

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`
- `REQUEST_TIMEOUT`
- `MAX_AGENT_STEPS`

当前无 `.env.example`、无 `.env`、无配置加载代码。

### 启动命令

**安装后（推荐）：**

```bash
python3 -m mini_agent.main
```

**未安装时（仅开发过渡）：**

```bash
PYTHONPATH=src python3 -m mini_agent.main
```

**预期输出：**

```text
Mini Agent Harness 0.0.0 started
```

### 测试命令

```bash
pytest
```

### Ruff 命令

```bash
ruff check .
ruff format --check .
```

### Mypy 命令

```bash
mypy src
```

## 10. 测试和质量检查状态

| 命令 | 状态 | 说明 |
|------|------|------|
| `pip install -e ".[dev]"` | **已运行并通过**（修复后） | 首次失败：hatchling 无法自动识别包；添加 `packages = ["src/mini_agent"]` 后成功 |
| `python3 -m mini_agent.main` | **已运行并通过** | 输出 `Mini Agent Harness 0.0.0 started` |
| `PYTHONPATH=src python -m mini_agent.main` | **已运行但失败** | `Command 'python' not found`（系统无 `python` 命令） |
| `PYTHONPATH=src python3 -m mini_agent.main` | **已运行并通过** | Task 1 阶段验证 |
| `pytest` | **已运行并通过** | `collected 0 items`，`no tests ran`，exit 0 |
| `ruff check .` | **已运行并通过** | `All checks passed!` |
| `ruff check . --fix` | **已运行并通过** | `All checks passed!` |
| `ruff format --check .` | **已运行但失败** | `Would reformat: src/mini_agent/__init__.py`、`src/mini_agent/main.py` |
| `mypy src` | **已运行并通过**（开发者终端） | `Success: no issues found in 2 source files` |

**交接核对时补充说明**：

- 生成交接文档时，在只读沙箱中 `mypy src` 出现 `INTERNAL ERROR`（可能与沙箱只读文件系统有关），**以开发者终端成功结果为准**。
- 生成交接文档时，在只读沙箱中 `pytest` 出现 cache 写入警告，但测试仍 0 项通过；**以开发者终端结果为准**。

## 11. 当前问题与技术债务

| 问题 | 当前影响 | 建议处理时机 |
|------|----------|--------------|
| `ruff format --check .` 未通过 | Week 01 最终验收要求 format check 通过 | Task 3 开始前或作为 Task 2 收尾小修复 |
| `README.md` 为空 | Week 01 完成标准要求 README 含安装与运行步骤 | Task 5 或 Task 3 后逐步补充 |
| `docs/plans/week-01-foundation.md` 任务状态未更新 | 计划文档与实际进度不一致，易误导新 Chat | 任意维护性 commit 时更新 |
| 版本号双重维护（`__init__.py` 与 `pyproject.toml`） | 未来可能版本不一致 | 未记录具体处理时机 |
| 无配置、日志、异常模块 | 无法加载环境变量、无统一错误处理 | Task 3、Task 4 |
| 无测试用例 | 仅有 pytest 发现能力，无回归保护 | Task 5 |
| 系统无 `python` 命令，仅 `python3` | 按文档执行 `python -m ...` 会失败 | 文档和验收命令统一写 `python3` |
| 本地 2 个 commit 未推送到 `origin/main` | 另一台电脑需 pull 或手动同步 | 迁移前 push 或拷贝仓库 |
| `.venv` 不在 Git 中 | 新电脑需重建虚拟环境 | 新环境按第 9 节初始化 |
| 设计原因/岗位方向未写入文档 | 新 Chat 无法从仓库推断业务背景 | 未记录 |

**已解决问题（供参考）**：

- Task 1 误提交 `__pycache__` → Task 2 已删除并加入 `.gitignore`
- `pip install -e ".[dev]"` hatchling 包发现问题 → 已通过 `packages = ["src/mini_agent"]` 修复

## 12. 当前唯一的下一项任务

### 任务名称

**Task 3：配置管理**

### 任务目标

- 通过环境变量加载配置
- 提供 `.env.example`
- 缺失必要配置时给出明确错误

### 为什么现在做

Task 1（包结构）和 Task 2（工具链与可安装性）已完成；配置管理是 Week 01 后续日志、异常和测试的基础，且 Month 01 后续 LLM Client 也需要统一配置入口。

### 涉及的文件或模块

**预计新建/修改**（实施前需先核对仓库）：

- `src/mini_agent/config.py`（或同等职责模块，名称实施时确定）
- `pyproject.toml`（添加 `pydantic-settings` 运行依赖）
- `.env.example`
- `.gitignore`（确认已包含 `.env`，当前已包含）
- 可能更新 `src/mini_agent/main.py`（仅当 Task 3 验收需要演示配置加载；避免提前做日志/Agent 逻辑）

### 推荐实施步骤

1. 核对 Git 状态与 Task 1/2 交付物。
2. 明确配置项与类型：`DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL`、`REQUEST_TIMEOUT`、`MAX_AGENT_STEPS`。
3. 选择配置模块路径与最小接口（建议单一 `Settings` 类，基于 `pydantic-settings`）。
4. 先写失败路径设计：缺失 API Key、类型错误、默认值行为。
5. 实现配置加载；添加 `.env.example`（不含真实密钥）。
6. 本地验证配置读取与失败场景。
7. 单独 commit（不与 Task 4/5 混合）。

### 测试场景

Task 3 计划文档未要求立即写 pytest 用例（完整测试在 Task 5），但开发过程中建议手动验证：

- 正确 `.env`/环境变量可读取
- 整数/浮点数转换正确
- 缺失 `DEEPSEEK_API_KEY` 时明确失败
- `.env` 不被 Git 跟踪

### 验收条件

- 正确配置可以被读取
- 整数和浮点数可以正确转换
- 缺失 API Key 时失败
- 真实 `.env` 不进入 Git

### 本任务暂时不做的内容

- 统一日志初始化（Task 4）
- 自定义异常类体系（Task 4）
- 正式 pytest 测试文件（Task 5）
- LLM API 调用（Week 2）
- CLI 参数解析
- 在日志中输出配置/Debug 信息（避免泄露敏感信息）

## 13. 后续计划概览

### 本周（Week 01）剩余任务

| Task | 内容 | 状态 |
|------|------|------|
| Task 3 | 配置管理（pydantic-settings、`.env.example`） | **下一步** |
| Task 4 | 日志与异常（`MiniAgentError` 等） | 未开始 |
| Task 5 | 配置测试 + 周末 Review + README 完善 | 未开始 |

**Week 01 完成定义**：`pytest`、`ruff check .`、`ruff format --check .`、`mypy src` 全部通过；README 含安装运行步骤；无真实 API Key 提交；核心模块职责可解释；Commit 按任务拆分。

### 本月（Month 01）后续阶段

| 周次 | 主题 |
|------|------|
| Week 2 | LLM Client（DeepSeek 非流式/流式、超时/限流/错误处理、Mock 测试） |
| Week 3 | Tool System 与 Agent Loop（工具注册、文件工具、Tool Calling、最大步骤限制） |
| Week 4 | Tracing、Evaluation、README、v0.1.0 交付 |

**注意**：新 Chat 一次只处理一个 Task，不要跨周批量实现。

## 14. 新 Chat 的工作限制

明确告诉新 Chat：

- **先核对交接内容与实际仓库**（目录、`git status`、`git log`、关键文件内容）。
- **不要立即修改代码**。
- **只处理「当前唯一的下一项任务」**（Task 3：配置管理）。
- **修改前先给出实施计划**（问题、职责、方案、步骤、验收）。
- **不要提前处理 Task 4/5 或 Week 2+ 内容**。
- **不要增加未经讨论的依赖**（Task 3 仅按计划引入 `pydantic-settings`）。
- **不要过度设计**（避免无需求的抽象/设计模式）。
- **开发者完成代码后先进行 Code Review**（区分必须修改/建议修改/可选优化）。
- **每次结束都给出测试和验收方法**。
- **默认角色是导师和审查者，不是代替开发者写完整实现**（除非开发者明确要求）。
- **不要输出或提交 API Key、Token、密码、真实 `.env` 内容**。

## 15. 给新 Cursor Chat 的启动指令

将以下内容原样粘贴到新的 Cursor Chat：

---

请先阅读我提供的《Mini Agent Harness 项目交接上下文》，然后只做项目状态核对，不要修改任何文件。

请按顺序执行：

1. 阅读交接上下文全文；
2. 检查实际目录结构、`git branch`、`git log -1`、`git status`、`git diff`；
3. 阅读 `.cursor/rules/` 下规则文件和 `docs/plans/` 下计划文件；
4. 核对交接信息是否与当前代码一致，重点检查：
   - Task 1/2 是否完成
   - 下一任务是否应为 Task 3
   - 质量检查命令的真实状态（尤其 `ruff format --check .`）
5. 输出以下四部分：
   - 项目目标与当前阶段
   - 已完成工作（基于 Git 与代码，不基于计划文档状态字段）
   - 当前问题与技术债务
   - 当前唯一的下一项任务（只能有一个）
6. 不要修改任何文件，不要安装依赖，不要执行与核对无关的操作；
7. 等我确认后，再给出 Task 3 的实施计划。

---

## 16. 信息可信度

### 已通过代码和 Git 验证的信息

- 当前分支、`HEAD` commit hash、工作区干净、ahead of origin 2 commits
- 已跟踪文件列表与目录结构
- `src/mini_agent/__init__.py`、`main.py`、`pyproject.toml`、`.gitignore` 的实际内容
- `README.md` 为空
- 无配置/日志/异常/LLM/工具/Agent 模块代码
- Git 提交历史与各 commit 涉及文件
- 开发者终端中运行过的命令及结果（见第 10 节）
- Python 3.14.4、Linux 环境、`.venv` 存在、`pip 25.1.1`
- 系统无 `python` 命令、有 `python3` 命令

### 只来自文档的信息

- Month 01 / Week 01 目标与任务拆分
- Task 3–5 及 Week 2–4 的验收标准
- 配置项名称与环境变量列表
- 异常类型命名计划（`MiniAgentError` 等）
- 本月/本周「暂时不做」的技术清单
- 月末验收问题列表
- 必须使用 pydantic-settings、不使用 LangChain/LangGraph

### 只来自当前对话的信息

- 开发者偏好：每个 task 单独 commit
- 开发者使用清华 PyPI 镜像（非项目硬性要求）
- Task 1 阶段曾用 `PYTHONPATH=src python3` 验证
- 理解检查中对设计决策的讨论结论（如 editable install 机制、Task 边界）
- WSL2 环境细节

### 尚未确认的信息

- 当前主要准备的岗位方向
- 异步/同步策略最终选择
- 配置模块最终文件命名与类设计
- 版本号单一来源方案
- 另一台电脑的具体操作系统与 Python 版本
- `origin/main` 远端是否已同步（仅确认本地 ahead 2 commits，未验证远端状态）
- Week 01 计划文档中任务状态字段为何未更新（原因未记录）
- `ruff format` 失败后是否已在本机格式化但未提交（当前 Git 干净，format check 仍失败，说明**未修复或未提交**）
```