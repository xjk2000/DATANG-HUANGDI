# 大唐皇帝 DATANG-HUANGDI

**用唐朝的制度智慧，治理 AI Agent 的协作混乱。**

一千三百年前，唐太宗设三省六部，以「中书取旨、门下封驳、尚书奉行」三权分立解决了一个古老问题——如何让庞大的行政体系高效运转，同时防止任何一环节失控。

今天，我们面对的问题惊人相似：当十几个 AI Agent 同时工作，谁来决策？谁来审核？谁来执行？谁来兜底？

**大唐皇帝**基于 [OpenClaw](https://openclaw.ai) 平台，将唐制三省六部五监映射为 16 个专职 AI Agent，构建了一套**制度驱动**的多 Agent 协作系统。

---

## 为什么需要这个？

多 Agent 系统最常见的三个问题：

1. **决策黑洞** —— Agent 自己决定做什么，没人审核，错了才发现
2. **职责混乱** —— 谁该写代码？谁该测试？Agent 之间互相推诿或越权
3. **不可观测** —— 十几个 Agent 同时跑，你不知道谁在干什么

大唐皇帝的解法：把唐朝治国两百年的制度经验搬过来——

- **中书省**负责理解你的意图、起草执行方案
- **门下省**负责找茬审核、封驳有问题的方案
- **尚书省**负责把审核通过的方案拆分派发给正确的部门
- **六部**负责管理型工作（HR、数据、协议、运维、测试、基建）
- **五监**负责生产型工作（后端开发、前端、安全、流计算、算法）

每个 Agent 只能和权限范围内的 Agent 通信，越权直接被拒。

---

## 系统组成

**三省 · 决策审核层（5 个 Agent）**

| 官职 | Agent ID | 做什么 |
|------|----------|--------|
| 中书令 | `zhongshuling` | 接你的旨意，分析拆解，起草敕令 |
| 中书舍人 | `zhongshu_sheren` | 辅助中书令，记录原始需求，整理分析报告 |
| 侍中侍郎 | `shizhong` | 门下省主官，审查敕令，拍板准奏或封驳 |
| 给事中 | `jishizhong` | 审查执行者，逐条排查敕令中的漏洞和风险 |
| 尚书令 | `shangshuling` | 接收准奏敕令，判断该派给谁，协调各部门 |

**六部 · 管理执行层（6 个 Agent）**

| 部门 | Agent ID | 对应现代职能 |
|------|----------|-------------|
| 吏部 | `libu` | Agent 生命周期管理——创建、授权、监控、销毁临时 Agent |
| 户部 | `hubu` | 数据库管理、日志查询、数据报表 |
| 礼部 | `libu_protocol` | API 规范定义、通信协议设计、对话标准 |
| 兵部 | `bingbu` | K8s 运维、CI/CD 流水线、网络拓扑、WAF |
| 刑部 | `xingbu` | 自动化测试、代码审计、Bug 溯源、异常 Agent 定责 |
| 工部 | `gongbu` | 公共类库维护、中间件标准化、脚手架 |

**五监 · 生产制造层（5 个 Agent）**

| 部门 | Agent ID | 产出 |
|------|----------|------|
| 将作监 | `jiangzuo` | 后端服务、业务逻辑（盖房子的） |
| 少府监 | `shaofu` | UI/UX、前端组件、可视化（做精巧器物的） |
| 军器监 | `junqi` | 加解密、防火墙、安全扫描（造兵器的） |
| 都水监 | `dushui` | Kafka 消息流、Flink 实时处理（理水路的） |
| 司农监 | `sinong` | 爬虫、模型训练、RAG 向量库（种地的） |

---

## 一条敕令的一生

当你对中书令说「帮我搭建一个用户认证服务」，背后发生的事：

```
 你（皇帝）
    │ "帮我搭建用户认证服务"
    ▼
 中书令 ←→ 中书舍人
    │ 分析需求，起草敕令：
    │ "将作监写 JWT 认证，军器监做加密，刑部写测试"
    ▼
 侍中侍郎 ←→ 给事中
    │ 审查发现：缺少 OAuth2 支持，密钥轮换方案不明确
    │ → 封驳，退回中书令补充
    ▼
 中书令（修改后重新提交）
    │ 补充 OAuth2 方案和密钥管理
    ▼
 侍中侍郎 → 准奏 ✅
    │
    ▼
 尚书令
    ├→ 将作监：编写 JWT + OAuth2 认证服务
    ├→ 军器监：实现 AES-256-GCM 加密 + 密钥轮换
    └→ 刑部：编写安全测试 + 漏洞扫描
         │
         ▼ 各部门完成后汇总
 尚书令 → 中书令 → 回奏给你
```

整个过程有 12 种状态、严格的状态机校验，非法跳转会被拒绝并写入审计日志。

---

## 通信管制

Agent 之间不是想聊就能聊的。权限矩阵确保分权制衡：

- **中书令**只能调用中书舍人（辅助）和侍中侍郎（送审）
- **侍中侍郎**可以退回中书令（封驳）或转交尚书令（准奏）
- **尚书令**可以调度所有六部和五监
- **六部 / 五监**只能回报尚书令，不能互相串联
- **皇帝（你）**默认通过中书令下旨，也可以直接指定任何 Agent

任何违反权限的调用都会被 OpenClaw 的 `subagents.allowAgents` 配置直接拦截。

---

## 安装与使用

**前置条件**：[OpenClaw](https://openclaw.ai) 已安装、Python 3.9+、macOS 或 Linux

### 基础安装

```bash
# 1. 克隆项目
git clone https://github.com/xjk2000/DATANG-HUANGDI.git
cd DATANG-HUANGDI

# 2. 一键安装（注册 16 Agent、部署人格文件、配置权限矩阵）
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

**状态机**：12 种敕令状态（Imperial → ZhongshuDraft → MenxiaReview → Approved → Dispatching → Executing → Done 等），合法转换白名单校验，非法跳转拒绝并记录审计日志。

**文件锁**：基于 `fcntl` 的跨进程文件锁，防止多 Agent 并发写入同一份任务数据。

**数据共享**：所有 Agent 的 workspace 通过软链接共享同一份 `data/` 和 `scripts/` 目录，确保数据一致。

**测试**：23 个端到端测试覆盖创建、状态流转、封驳重提、非法跳转拒绝、取消、阻塞恢复等场景。

---

## 目录说明

```
agents/          16 个 Agent 的 SOUL.md 人格文件
dashboard/       翰林院看板（server.py + index.html）
scripts/         看板 CLI、文件锁、数据同步脚本
tests/           端到端测试
install.sh       一键安装
Dockerfile       容器化支持
```

---

## License

MIT · 作者：XuJiaKai
