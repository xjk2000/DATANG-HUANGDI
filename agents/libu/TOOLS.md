# TOOLS.md - 吏部工具配置

## 看板 CLI

```bash
python3 __REPO_DIR__/scripts/kanban_update.py state <id> <state> "<说明>"
python3 __REPO_DIR__/scripts/kanban_update.py progress <id> "<当前动态>" "<计划清单>"
```

## Agent 管理

```bash
# 查看 Agent 列表
openclaw agents list 2>/dev/null
cat ~/.openclaw/openclaw.json | python3 -m json.tool

# 搜索 Agent 工作区
find ~/.openclaw/ -name "SOUL.md" -type f
```

## 环境信息

- 项目仓库：`__REPO_DIR__`
- OpenClaw 配置：`~/.openclaw/openclaw.json`
- Python：`python3`
