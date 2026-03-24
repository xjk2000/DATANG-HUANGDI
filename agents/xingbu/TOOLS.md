# TOOLS.md - 刑部工具配置

## 看板 CLI

```bash
python3 __REPO_DIR__/scripts/kanban_update.py state <id> <state> "<说明>"
python3 __REPO_DIR__/scripts/kanban_update.py progress <id> "<当前动态>" "<计划清单>"
```

## QA 审计工具

```bash
# 运行测试
cd __REPO_DIR__ && python3 -m pytest tests/ -v
python3 __REPO_DIR__/tests/test_kanban.py

# 代码审计
rg "TODO\|FIXME\|HACK\|XXX" __REPO_DIR__ --type py
rg "eval\|exec\|os.system\|subprocess.call" __REPO_DIR__ --type py

# 语法检查
python3 -m py_compile <file>
find __REPO_DIR__ -name "*.py" -exec python3 -m py_compile {} \;

# 测试覆盖
find __REPO_DIR__/tests -name "*.py" -type f
```

## 环境信息

- 项目仓库：`__REPO_DIR__`
- 测试目录：`__REPO_DIR__/tests/`
- Python：`python3`
