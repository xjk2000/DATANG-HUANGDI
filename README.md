# 大唐皇帝 DATANG-HUANGDI

**用唐朝的制度智慧，治理 AI Agent 的协作混乱。**

一千三百年前，唐太宗设三省六部，以「中书取旨、门下封驳、尚书奉行」三权分立解决了一个古老问题——如何让庞大的行政体系高效运转，同时防止任何一环节失控。

今天，我们面对的问题惊人相似：当十几个 AI Agent 同时工作，谁来决策？谁来审核？谁来执行？谁来兜底？

**大唐皇帝**基于 [OpenClaw](https://openclaw.ai) 平台，将唐制三省六部五监映射为 16 个专职 AI Agent，其中 6 个核心 Agent 担当日常流转，其余可通过自建调度随时激活，构建了一套**制度驱动**的多 Agent 协作系统。

---

## 为什么需要这个？

多 Agent 系统最常见的三个问题：

1. **决策黑洞** —— Agent 自己决定做什么，没人审核，错了才发现
2. **职责混乱** —— 谁该写代码？谁该测试？Agent 之间互相推诿或越权
3. **不可观测** —— 十几个 Agent 同时跑，你不知道谁在干什么

大唐皇帝的解法：保留完整三省六部五监体系，同时精简日常流转为 6 个核心 Agent——

**核心流转（6 Agent）：**
- **中书令**负责接旨、分析、起草、审核、回奏
- **尚书令**负责结构化任务拆分、派发、监控、汇总
- **将作监**负责后端开发 + 基建
- **少府监**负责前端与交互
- **刑部**负责测试 + 审计 + 安全
- **户部**负责数据 + 日志 + 运维

**完整体系（16 Agent 全部注册）：**
三省六部五监全部保留，通过 `agent_invoke.py` 自建调度可随时激活任意 Agent。

每个 Agent 只能和权限范围内的 Agent 通信，越权直接被拒。

---

## 系统组成

**核心流转（6 Agent）**

| 官职 | Agent ID | 做什么 |
|------|----------|--------|
| 中书令 | `zhongshuling` | 接旨 + 分析 + 起草 + 审核 + 回奏 |
| 尚书令 | `shangshuling` | 结构化任务拆分 + 派发 + 监控 + 汇总 |
| 将作监 | `jiangzuo` | 后端开发 + 基建 |
| 少府监 | `shaofu` | 前端与交互 |
| 刑部 | `xingbu` | 测试 + 审计 + 安全 |
| 户部 | `hubu` | 数据 + 日志 + 运维 |

**完整三省六部五监（16 Agent）**

| 层级 | 官职 | Agent ID | 职能 |
|------|------|----------|------|
| 中书省 | 中书舍人 | `zhongshu_sheren` | 辅助中书令分析 |
| 门下省 | 侍中侍郎 | `shizhong` | 审查敕令，准奏或封驳 |
| 门下省 | 给事中 | `jishizhong` | 逐条排查漏洞 |
| 六部 | 吏部 | `libu` | Agent 生命周期管理 |
| 六部 | 礼部 | `libu_protocol` | API 规范、通信协议 |
| 六部 | 兵部 | `bingbu` | K8s 运维、CI/CD |
| 六部 | 工部 | `gongbu` | 公共类库、中间件 |
| 五监 | 军器监 | `junqi` | 加解密、安全工具 |
| 五监 | 都水监 | `dushui` | Kafka 消息流、Flink |
| 五监 | 司农监 | `sinong` | 爬虫、模型训练、RAG |

> 完整体系全部注册，通过 `agent_invoke.py` 可随时唤起任意 Agent。

---

## 一条敕令的一生

当你对中书令说「帮我搭建一个用户认证服务」，背后发生的事：

```
 你（皇帝）
    │ "帮我搭建用户认证服务"
    ▼
 中书令
    │ 分析需求 + 起草敕令 + 自审通过
    │ "将作监写 JWT+OAuth2，刑部做安全测试"
    ▼
 尚书令
    │ task_dispatch.py 结构化派发
    ├→ 将作监：编写 JWT + OAuth2 认证服务
    └→ 刑部：编写安全测试 + 漏洞扫描
         │
         ▼ 各部门用 task_dispatch.py report 回报
 尚书令（汇总）→ 中书令 → 回奏给你
```

流程从原来的 5 层精简为 3 层（中书令 → 尚书令 → 执行部门），减少交接損耗，加快执行速度。

状态机校验仍然严格，非法跳转会被拒绝并写入审计日志。

---

## 通信管制

Agent 之间不是想聊就能聊的。权限矩阵确保分权制衡：

- **中书令** ↔ 尚书令（双向通信）
- **尚书令** → 将作监 / 少府监 / 刑部 / 户部（单向派发）
- **执行部门**只能回报尚书令，不能互相串联
- **皇帝（你）**默认通过中书令下旨，也可以直接指定任何 Agent

### 自建调度机制

系统不依赖 OpenClaw 的 `subagents` 通信，而是通过 `agent_invoke.py` 自建调度：

```bash
# 唤起目标 agent 并传递任务
python3 scripts/agent_invoke.py invoke <source> <target> "任务描述" --edict CL-xxx

# 查看敕令调度链路
python3 scripts/agent_invoke.py chain CL-xxx

# 查看调度日志
python3 scripts/agent_invoke.py log
```

每次调度都会记录到 `data/invoke_log.json`，管理系统可完整监控调度链路。

同时 OpenClaw 的 `subagents.allowAgents` 权限矩阵仍然生效，作为安全底线。

---

## 安装与使用

**前置条件**：[OpenClaw](https://openclaw.ai) 已安装、Python 3.9+、macOS 或 Linux

### 基础安装

```bash
# 1. 克隆项目
git clone https://github.com/xjk2000/DATANG-HUANGDI.git
cd DATANG-HUANGDI

# 2. 一键安装（注册 6 Agent、部署人格文件、配置权限矩阵）
chmod +x install.sh && ./install.sh

# 3. 启动翰林院看板（可选）
python3 dashboard/server.py        # 浏览器打开 http://127.0.0.1:7891
bash scripts/run_loop.sh &         # 后台运行数据刷新

# 4. 开始下旨
openclaw chat --agent zhongshuling
```

### 环境变量配置（可选）

项目支持通过环境变量自定义路径，适用于 Docker、多用户环境或自定义安装位置：

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑配置（可选）
# OPENCLAW_HOME=/custom/path/to/openclaw  # 默认为 ~/.openclaw
# REPO_DIR=/custom/path/to/claw-diwang    # 默认为项目根目录

# 加载环境变量
source .env

# 运行安装
./install.sh
```

**环境变量说明**：

- `OPENCLAW_HOME` - OpenClaw 安装目录（默认：`~/.openclaw`）
- `REPO_DIR` - 帝王系统项目根目录（默认：脚本所在目录）

这使得项目可以在不同环境中灵活部署，无需修改代码。

你也可以跳过三省流程，直接对具体 Agent 下令：

```bash
openclaw chat --agent jiangzuo     # 直接找将作监写代码
openclaw chat --agent xingbu       # 直接找刑部做审计
```

---

## SLS 日志诊断（刑部 + 户部联动）

系统内置了**代码 → 日志**的完整诊断链路：刑部从源码中提取真实日志关键词，户部用这些关键词精确查询 SLS，避免凭空猜测查询语句。

### 第一步：配置 `data/diwang.json`

安装时会自动创建此文件，填入两项关键配置：

```json
{
  "project_dir": "/path/to/your/project",

  "sls": {
    "get_logs_script": "~/projects/get_logs.py",
    "service_filter":  "service:shulex-intelli",
    "environments": {}
  }
}
```

| 字段 | 说明 |
|------|------|
| `project_dir` | 被监控项目的代码根目录（刑部搜索源码用） |
| `sls.get_logs_script` | 已有 SLS 查询脚本路径（带凭证，默认 `~/projects/get_logs.py`） |
| `sls.service_filter` | 自动追加到每条查询的服务过滤器 |

> 参考示例：`diwang.json.example`

---

### 第二步：刑部——从源码提取日志关键词

让刑部（或直接手动）运行 `analyze-logs`，从项目代码中找出该功能真实打印的日志内容：

```bash
python3 scripts/sls_query.py analyze-logs <功能关键词>

# 示例
python3 scripts/sls_query.py analyze-logs UserLogin
python3 scripts/sls_query.py analyze-logs OrderCreate
```

**输出示例：**

```
🔍 代码日志分析: [UserLogin]
   项目路径: /path/to/your/project
────────────────────────────────────────────────────────────────
📄 找到 2 条日志语句:

  [1] [java] .../UserLoginService.java:45
       log.info("用户登录成功: userId={}", userId);
       → 日志内容: "用户登录成功"

  [2] [java] .../UserLoginService.java:68
       log.error("登录失败: invalid credentials");
       → 日志内容: "登录失败"

────────────────────────────────────────────────────────────────
💡 推荐 SLS 查询关键词（直接传给户部）:
   "用户登录成功"
   "登录失败"

📋 示例（生产环境，最近 1 小时）:
   python3 scripts/sls_query.py production \
     "2025-01-01 00:00:00" "2025-01-01 01:00:00" \
     '"用户登录成功" OR "登录失败"'
```

支持 Java / Python / TypeScript / Go 项目，自动降级到 `grep`（若无 `rg`）。

---

### 第三步：户部——用真实关键词查 SLS

```bash
# 用法：python3 scripts/sls_query.py <环境> "<开始>" "<结束>" "<查询语句>" [--out <文件>]

# 生产环境，用刑部提取的精确关键词
python3 scripts/sls_query.py production \
  "2025-01-01 00:00:00" "2025-01-01 01:00:00" \
  '"用户登录成功" OR "登录失败"'

# 查 ERROR 日志
python3 scripts/sls_query.py production \
  "2025-01-01 00:00:00" "2025-01-01 01:00:00" \
  "UserLogin AND level:ERROR"

# 输出太长时落盘，避免刷屏
python3 scripts/sls_query.py production \
  "2025-01-01 00:00:00" "2025-01-01 01:00:00" \
  "level:ERROR" --out /tmp/sls_err.log

# 测试环境
python3 scripts/sls_query.py staging \
  "2025-01-01 00:00:00" "2025-01-01 01:00:00" \
  "OrderCreate"
```

> `service:shulex-intelli` 会自动追加到每条查询，无需手动加。

---

### 完整诊断工作流（「查询某功能是否正常」）

```
你对中书令下旨："检查 UserLogin 功能是否正常"
           │
           ▼
      尚书令并行派发
      ├── 刑部
      │   ① analyze-logs UserLogin
      │      → 找到 "用户登录成功"、"登录失败"
      │   ② 搜索代码：实现文件、异常处理、测试覆盖
      │   → 返回：代码分析 + 日志关键词
      │
      └── 户部（收到刑部的日志关键词后）
          ③ query '"用户登录成功" OR "登录失败"'
             → 精确匹配，结果比模糊搜索准 10 倍
          → 返回：SLS 查询报告
           │
           ▼
      尚书令汇总 → 综合结论回奏
```

---

## 翰林院看板

安装后访问 `http://127.0.0.1:7891`，可以看到：

- **敕令看板** —— 所有任务按状态分栏展示，实时心跳检测
- **省部调度** —— 16 个 Agent 的活跃状态和会话数
- **奏折阁** —— 已完成敕令的归档和完整流转记录
- **审计日志** —— 每一次状态变更、流转、封驳的完整记录

看板服务器用纯 Python 标准库实现，零外部依赖。也支持 Docker 部署：

```bash
docker compose up -d
```

---

## 技术细节

**状态机**：12 种敕令状态（Imperial → ZhongshuDraft → Approved → Dispatching → Executing → Done 等），合法转换白名单校验，非法跳转拒绝并记录审计日志。

**结构化调度**：`task_dispatch.py` 提供 `dispatch`、`report`、`status` 三个命令，确保任务派发和回报全程可追溯。

**自建调度**：`agent_invoke.py` 提供 `invoke`、`chain`、`log`、`history` 四个命令，不依赖 OpenClaw subagents 通信，Agent 通过脚本唤起其他 Agent 并携带会话上下文，调度链路全程可监控。

**文件锁**：基于 `fcntl` 的跨进程文件锁，防止多 Agent 并发写入同一份任务数据。

**数据共享**：所有 Agent 的 workspace 通过软链接共享同一份 `data/` 和 `scripts/` 目录，确保数据一致。

**测试**：23 个端到端测试覆盖创建、状态流转、非法跳转拒绝、取消、阻塞恢复等场景。

---

## 目录说明

```
agents/          16 个 Agent 的 SOUL.md 人格文件
dashboard/       翰林院看板（server.py + index.html）
scripts/         看板 CLI、任务调度、Agent 调度、文件锁、数据同步
tests/           端到端测试
install.sh       一键安装
Dockerfile       容器化支持
```

---

## License

MIT · 作者：XuJiaKai
