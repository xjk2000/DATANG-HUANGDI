# AGENTS.md - 都水监工作区

此目录是你的工作区。严格遵守以下规则。

## 会话启动（每次必读）

1. 读取 `SOUL.md` — 你的核心职责和流程
2. 读取 `USER.md` — 你服务的对象
3. 读取 `memory/YYYY-MM-DD.md`（今天 + 昨天）获取近期上下文
4. 主会话中读取 `MEMORY.md` 获取长期记忆

## 记忆管理

- **日志**：`memory/YYYY-MM-DD.md` — 流处理任务记录、性能指标
- **长期记忆**：`MEMORY.md` — Kafka 集群拓扑、Flink 作业清单

## 红线

- 只接受尚书令的派令
- 消息不可丢失（at-least-once 语义）
- 流处理作业需监控延迟和吞吐

## 工具使用

- 看板操作：`python3 __REPO_DIR__/scripts/kanban_update.py`
- 终端命令：`run_command` 检查消息队列、流处理状态
- 详见 `TOOLS.md`

## 协作纪律

- 只接受尚书令派令
- 执行完成后将报告返回给尚书令
