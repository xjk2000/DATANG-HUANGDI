# TOOLS.md - 侍中侍郎工具配置

## 看板 CLI

```bash
python3 __REPO_DIR__/scripts/kanban_update.py state <id> <state> "<说明>"
python3 __REPO_DIR__/scripts/kanban_update.py flow <id> "<from>" "<to>" "<remark>"
python3 __REPO_DIR__/scripts/kanban_update.py progress <id> "<当前动态>" "<计划清单>"
```

## 终端搜索

```bash
rg "关键词" __REPO_DIR__ --type py
find __REPO_DIR__ -maxdepth 3 -type f | head -60
```

## 数据文件

- 任务数据：`__REPO_DIR__/data/tasks.json`
- 审计日志：`__REPO_DIR__/data/audit.log`

## 环境信息

- 项目仓库：`__REPO_DIR__`
- 看板服务：`http://127.0.0.1:7891`
- Python：`python3`
