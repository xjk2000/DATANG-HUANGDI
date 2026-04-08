# TOOLS.md - 礼部工具配置

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

## API 规范工具

```bash
# 搜索接口定义
rg "def \|class \|@app\.\|@router" __REPO_DIR__ --type py
find __REPO_DIR__ -name "*.yaml" -o -name "*.json" -type f | head -20

# 验证 JSON 语法
python3 -c "import json; json.load(open('文件路径'))"
```

## 环境信息

- 项目仓库：`__REPO_DIR__`
- Python：`python3`
