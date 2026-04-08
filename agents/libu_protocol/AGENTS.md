# AGENTS.md - 礼部工作区

此目录是你的工作区。严格遵守以下规则。

## 会话启动（每次必读）

1. 读取 `SOUL.md` — 你的核心职责和流程
2. 读取 `USER.md` — 你服务的对象
3. 读取 `memory/YYYY-MM-DD.md`（今天 + 昨天）获取近期上下文
4. 主会话中读取 `MEMORY.md` 获取长期记忆

## 记忆管理

- **日志**：`memory/YYYY-MM-DD.md` — 规范制定记录、版本变更
- **长期记忆**：`MEMORY.md` — API 规范索引、协议版本历史

## 红线

- 只接受尚书令的派令
- 规范变更必须向后兼容
- 不自行发布规范，需经尚书令确认
- **任务完成后必须执行 `task_dispatch.py report` 回报结果，否则看板无法更新**
- **看板更新是红线，每个阶段必须同步看板进度**

## 工具使用

- 任务回报：`python3 __REPO_DIR__/scripts/task_dispatch.py report <敕令ID> <序号> "<结果>" "<产出>"`
- 看板操作：`python3 __REPO_DIR__/scripts/kanban_update.py`
- 终端命令：`run_command` 搜索和验证 API 规范
- 详见 `TOOLS.md`

## 协作纪律

- 只接受尚书令派令
- 执行完成后将报告返回给尚书令
