# TOOLS.md - 尚书令工具配置

## 结构化任务调度（必用）

```bash
# 派发子任务（自动创建看板 todo + 输出派令模板）
python3 __REPO_DIR__/scripts/task_dispatch.py dispatch <敕令ID> <agent_id> "<任务描述>" "<验收标准>"

# 查看敕令所有子任务状态
python3 __REPO_DIR__/scripts/task_dispatch.py status <敕令ID>
```

## Agent 调度（唤起执行部门）

> **🚨 必须通过 agent_invoke.py 唤起执行部门，不要用 subagent 直接调用！**

```bash
# 唤起执行部门（同步等待结果）
python3 __REPO_DIR__/scripts/agent_invoke.py invoke shangshuling <agent_id> "派令内容" --edict CL-xxx

# 异步唤起（并行派发多个部门）
python3 __REPO_DIR__/scripts/agent_invoke.py invoke shangshuling jiangzuo "任务A" --edict CL-xxx --async
python3 __REPO_DIR__/scripts/agent_invoke.py invoke shangshuling xingbu "任务B" --edict CL-xxx --async

# 查看敕令调度链路
python3 __REPO_DIR__/scripts/agent_invoke.py chain CL-xxx

# 查看最近调度日志
python3 __REPO_DIR__/scripts/agent_invoke.py log
```

## 看板 CLI

```bash
python3 __REPO_DIR__/scripts/kanban_update.py state <id> <state> "<说明>"
python3 __REPO_DIR__/scripts/kanban_update.py flow <id> "<from>" "<to>" "<remark>"
python3 __REPO_DIR__/scripts/kanban_update.py progress <id> "<当前动态>" "<计划清单>"
python3 __REPO_DIR__/scripts/kanban_update.py done <id> "<output>" "<summary>"
python3 __REPO_DIR__/scripts/kanban_update.py list
```

## 终端搜索

```bash
rg "关键词" __REPO_DIR__
find __REPO_DIR__ -maxdepth 3 -type f | head -80
```

## 部门 Agent ID 速查

**核心执行部门（常用）：**

| 部门 | Agent ID | 职责 |
|------|---------|------|
| 将作监 | `jiangzuo` | 后端开发 + 基建 |
| 少府监 | `shaofu` | 前端与交互 |
| 刑部 | `xingbu` | 测试 + 审计 + 安全 |
| 户部 | `hubu` | 数据 + 日志 + 运维 |

**完整三省六部五监（可通过 agent_invoke.py 扩展激活）：**

| 部门 | Agent ID | 职责 |
|------|---------|------|
| 中书舍人 | `zhongshu_sheren` | 辅助中书令分析 |
| 侍中侍郎 | `shizhong` | 门下省审查 |
| 给事中 | `jishizhong` | 逐条排查漏洞 |
| 吏部 | `libu` | Agent 生命周期管理 |
| 礼部 | `libu_protocol` | API 规范 + 协议 |
| 兵部 | `bingbu` | K8s 运维 + CI/CD |
| 工部 | `gongbu` | 公共类库 + 中间件 |
| 军器监 | `junqi` | 加解密 + 安全工具 |
| 都水监 | `dushui` | Kafka + Flink 流处理 |
| 司农监 | `sinong` | 爬虫 + 模型训练 + RAG |

## 心跳监控（发现卡死 Agent）

```bash
# 查看所有 Agent 实时状态（Claude Code CLI 和 OpenClaw 共享）
python3 __REPO_DIR__/scripts/agent_heartbeat.py status

# 检测卡死 Agent（10 分钟无心跳）
python3 __REPO_DIR__/scripts/agent_heartbeat.py check --timeout 600

# 查看单个 Agent 详情
python3 __REPO_DIR__/scripts/agent_heartbeat.py status --agent jiangzuo
```

## 数据文件

- 任务数据：`__REPO_DIR__/data/tasks_source.json`
- 派发记录：`__REPO_DIR__/data/dispatch_log.json`
- 审计日志：`__REPO_DIR__/data/kanban_audit.log`

## 环境信息

- 项目仓库：`__REPO_DIR__`
- 看板服务：`http://127.0.0.1:7891`
- Python：`python3`
