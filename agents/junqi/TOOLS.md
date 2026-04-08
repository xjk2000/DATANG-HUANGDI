# TOOLS.md - 军器监工具配置

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

## 安全工具

```bash
# 代码安全扫描
rg "eval\|exec\|os.system\|subprocess\|pickle.load\|yaml.load" __REPO_DIR__ --type py
rg "password\|secret\|token\|api_key" __REPO_DIR__ -i

# 文件权限
find __REPO_DIR__ -perm -o+w -type f 2>/dev/null
ls -la __REPO_DIR__/data/

# 网络安全
ss -ltnp | head -20
curl -s http://127.0.0.1:7891/api/health

# 依赖安全
pip3 audit 2>/dev/null || pip3 list 2>/dev/null
```

## 环境信息

- 项目仓库：`__REPO_DIR__`
- Python：`python3`
