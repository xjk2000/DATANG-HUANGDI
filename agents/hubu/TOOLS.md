# TOOLS.md - 户部工具配置

## 看板 CLI

```bash
python3 __REPO_DIR__/scripts/kanban_update.py state <id> <state> "<说明>"
python3 __REPO_DIR__/scripts/kanban_update.py progress <id> "<当前动态>" "<计划清单>"
```

## 数据管理

```bash
# 查看数据文件
find __REPO_DIR__/data -type f
cat __REPO_DIR__/data/tasks.json | python3 -m json.tool

# 日志搜索
rg "ERROR\|WARN" __REPO_DIR__/data/
tail -200 __REPO_DIR__/data/audit.log

# 磁盘用量
du -sh __REPO_DIR__/data/*

# 数据备份
cp __REPO_DIR__/data/tasks.json __REPO_DIR__/data/tasks.json.bak
```

## 环境信息

- 项目仓库：`__REPO_DIR__`
- 数据目录：`__REPO_DIR__/data/`
- Python：`python3`
