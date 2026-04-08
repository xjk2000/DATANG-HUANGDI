# TOOLS.md - 司农监工具配置

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

## 数据与算法工具

```bash
# 搜索数据处理代码
rg "model\|train\|embedding\|vector\|crawl" __REPO_DIR__ --type py -i
find __REPO_DIR__ -name "*.csv" -o -name "*.parquet" -o -name "*.pkl" -type f

# Python ML 环境
python3 --version
pip3 list 2>/dev/null | rg "torch\|numpy\|pandas\|scikit\|transformers" -i

# 数据文件分析
wc -l __REPO_DIR__/data/*.json 2>/dev/null
du -sh __REPO_DIR__/data/
```

## 环境信息

- 项目仓库：`__REPO_DIR__`
- 数据目录：`__REPO_DIR__/data/`
- Python：`python3`
