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

## SLS 日志查询

**接口：** `python3 sls_query.py <环境> "<开始时间>" "<结束时间>" "<查询语句>" [--out <文件>]`

```bash
# 环境: production/prod（生产） staging/test（测试）

# 用刑部提取的精确日志内容查询（最推荐）
python3 __REPO_DIR__/scripts/sls_query.py production \
  "2025-01-01 00:00:00" "2025-01-01 01:00:00" \
  '"用户登录成功" OR "登录失败"'

# 用功能关键词宽泛查询
python3 __REPO_DIR__/scripts/sls_query.py production \
  "2025-01-01 00:00:00" "2025-01-01 01:00:00" \
  "UserLogin"

# 查 ERROR
python3 __REPO_DIR__/scripts/sls_query.py production \
  "2025-01-01 00:00:00" "2025-01-01 01:00:00" \
  "UserLogin AND level:ERROR"

# 输出较长时落盘（避免刷屏）
python3 __REPO_DIR__/scripts/sls_query.py production \
  "2025-01-01 00:00:00" "2025-01-01 01:00:00" \
  "level:ERROR" --out /tmp/sls_err.log

# 测试环境
python3 __REPO_DIR__/scripts/sls_query.py staging \
  "2025-01-01 00:00:00" "2025-01-01 01:00:00" \
  "OrderCreate"
```

> 注：脚本会自动将 `service:shulex-intelli` 追加到查询语句中。

**配置：** 编辑 `__REPO_DIR__/data/diwang.json`，确认 `sls.get_logs_script` 路径正确。

> 配置示例详见 `__REPO_DIR__/diwang.json.example`

## 环境信息

- 项目仓库：`__REPO_DIR__`
- 数据目录：`__REPO_DIR__/data/`
- 配置文件：`__REPO_DIR__/data/diwang.json`（安装时已创建）
- 配置示例：`__REPO_DIR__/diwang.json.example`
- Python：`python3`
