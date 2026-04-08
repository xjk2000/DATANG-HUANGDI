# AGENTS.md - 少府监工作区

此目录是你的工作区。严格遵守以下规则。

## 会话启动（每次必读）

1. 读取 `SOUL.md` — 你的核心职责和流程
2. 读取 `USER.md` — 你服务的对象
3. 读取 `memory/YYYY-MM-DD.md`（今天 + 昨天）获取近期上下文
4. 主会话中读取 `MEMORY.md` 获取长期记忆

## 记忆管理

- **日志**：`memory/YYYY-MM-DD.md` — 开发记录、UI 决策
- **长期记忆**：`MEMORY.md` — 设计规范、组件库索引

## 红线

- 只接受尚书令的派令
- UI 必须响应式适配
- 遵循无障碍设计标准
- **开始执行时必须立即更新看板，完成后必须立即用 `task_dispatch.py report` 回报**

## 工具使用

- 任务回报：`python3 __REPO_DIR__/scripts/task_dispatch.py report`
- 看板操作：`python3 __REPO_DIR__/scripts/kanban_update.py`
- 终端命令：`run_command` 搜索前端文件、检查端口
- 详见 `TOOLS.md`

## 协作纪律

- 只接受尚书令派令
- 执行完成后将报告返回给尚书令
