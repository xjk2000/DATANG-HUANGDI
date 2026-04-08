# TOOLS.md - 中书令工具配置

## Agent 调度（唤起其他 Agent）

> **🚨 必须通过 agent_invoke.py 唤起其他 Agent，不要用 subagent 直接调用！**

```bash
# 唤起尚书令派发敕令（同步等待结果）
python3 __REPO_DIR__/scripts/agent_invoke.py invoke zhongshuling shangshuling "敕令内容..." --edict CL-xxx --context "完整敕令文书"

# 异步唤起（不等待结果）
python3 __REPO_DIR__/scripts/agent_invoke.py invoke zhongshuling shangshuling "敕令内容..." --edict CL-xxx --async

# 查看敕令调度链路
python3 __REPO_DIR__/scripts/agent_invoke.py chain CL-xxx

# 查看调度日志
python3 __REPO_DIR__/scripts/agent_invoke.py log
```

**通信规则**：
- 中书令主要唤起：尚书令
- 不可直接唤起执行部门（必须通过尚书令转达）

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
