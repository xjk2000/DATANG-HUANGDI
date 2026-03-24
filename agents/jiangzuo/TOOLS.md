# TOOLS.md - 将作监工具配置

## 看板 CLI

```bash
python3 __REPO_DIR__/scripts/kanban_update.py state <id> <state> "<说明>"
python3 __REPO_DIR__/scripts/kanban_update.py progress <id> "<当前动态>" "<计划清单>"
```

## 开发工具

```bash
# 搜索代码
rg "def \|class \|async def " __REPO_DIR__ --type py
find __REPO_DIR__ -name "*.py" -type f

# 运行测试
cd __REPO_DIR__ && python3 -m pytest tests/ -v

# Git 操作
cd __REPO_DIR__ && git status
cd __REPO_DIR__ && git diff --stat
cd __REPO_DIR__ && git log --oneline -5
```

## 环境信息

- 项目仓库：`__REPO_DIR__`
- Python：`python3`
