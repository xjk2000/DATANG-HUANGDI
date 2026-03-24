# TOOLS.md - 中书舍人工具配置

## 看板 CLI

```bash
python3 __REPO_DIR__/scripts/kanban_update.py progress <id> "<当前动态>" "<计划清单>"
```

## 终端搜索

```bash
rg "关键词" __REPO_DIR__ --type py
find __REPO_DIR__ -name "*.md" -type f
find __REPO_DIR__ -maxdepth 2 -type f | head -50
```

## 数据文件

- 任务数据：`__REPO_DIR__/data/tasks.json`

## 环境信息

- 项目仓库：`__REPO_DIR__`
- Python：`python3`
