# TOOLS.md - 工部工具配置

## 任务回报

```bash
# 完成后回报结果（红线！必须执行）
python3 __REPO_DIR__/scripts/task_dispatch.py report <敕令ID> <子任务序号> "<执行结果>" "<产出物>"
```

## 看板 CLI

```bash
python3 __REPO_DIR__/scripts/kanban_update.py state <id> <state> "<说明>"
python3 __REPO_DIR__/scripts/kanban_update.py progress <id> "<当前动态>" "<计划清单>"
```

## 开发工具

```bash
# 搜索公共类库
rg "def \|class " __REPO_DIR__/scripts/ --type py
find __REPO_DIR__ -name "utils*" -o -name "common*" -type f

# 依赖管理
cat __REPO_DIR__/requirements.txt 2>/dev/null
pip3 list 2>/dev/null | head -30

# 代码分析
find __REPO_DIR__ -name "*.py" -type f | xargs wc -l | sort -n
```

## 环境信息

- 项目仓库：`__REPO_DIR__`
- 脚本目录：`__REPO_DIR__/scripts/`
- Python：`python3`
