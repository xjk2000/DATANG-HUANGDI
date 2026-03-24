# TOOLS.md - 中书令工具配置

## 朝堂会话 CLI（跨 Agent 通信）

```bash
# 发送消息给中书舍人（请求分析）
python3 __REPO_DIR__/scripts/session/cli.py send zhongshuling zhongshu_sheren <task_id> request "请分析此旨意并拆解为可执行子任务"

# 提交敕令给侍中侍郎（门下审议）
python3 __REPO_DIR__/scripts/session/cli.py send zhongshuling shizhong <task_id> edict "敕令内容..."

# 查看收件箱
python3 __REPO_DIR__/scripts/session/cli.py inbox zhongshuling

# 查看单条消息
python3 __REPO_DIR__/scripts/session/cli.py read zhongshuling <msg_id>

# 回复消息
python3 __REPO_DIR__/scripts/session/cli.py reply zhongshuling <ref_msg_id> "回复内容"

# 确认消息已处理
python3 __REPO_DIR__/scripts/session/cli.py ack zhongshuling <msg_id>

# 查看任务会话线程
python3 __REPO_DIR__/scripts/session/cli.py thread <task_id>

# 查看路由表（谁可以给谁发消息）
python3 __REPO_DIR__/scripts/session/cli.py routes zhongshuling
```

**消息类型**：
- `edict` — 敕令下达
- `request` — 请求协助
- `reply` — 正常回复
- `reject` — 封驳（门下省专用）
- `report` — 执行报告

**通信规则**：
- 中书令可发送给：中书舍人、侍中侍郎
- 中书令接收来自：皇帝、侍中侍郎、中书舍人

## 看板 CLI

```bash
# 创建任务
python3 __REPO_DIR__/scripts/kanban_update.py create <id> "<标题>" <state> <org> <official>

# 状态流转
python3 __REPO_DIR__/scripts/kanban_update.py state <id> <state> "<说明>"

# 流转记录
python3 __REPO_DIR__/scripts/kanban_update.py flow <id> "<from>" "<to>" "<remark>"

# 进度更新
python3 __REPO_DIR__/scripts/kanban_update.py progress <id> "<当前动态>" "<计划清单>"

# 完成任务
python3 __REPO_DIR__/scripts/kanban_update.py done <id> "<output>" "<summary>"
```

## 终端搜索

```bash
# ripgrep（推荐）
rg "关键词" __REPO_DIR__ --type py

# find 搜索文件名
find __REPO_DIR__ -name "*.py" -type f

# grep 回退
grep -rn "关键词" __REPO_DIR__/ --include="*.py"
```

## 数据文件

- 任务数据：`__REPO_DIR__/data/tasks.json`
- 审计日志：`__REPO_DIR__/data/audit.log`
- Agent 配置：`__REPO_DIR__/data/agent_config.json`
- 实时状态：`__REPO_DIR__/data/live_status.json`

## 环境信息

- 项目仓库：`__REPO_DIR__`
- 看板服务：`http://127.0.0.1:7891`
- Python：`python3`
