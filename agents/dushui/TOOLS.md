# TOOLS.md - 都水监工具配置

## 看板 CLI

```bash
python3 __REPO_DIR__/scripts/kanban_update.py state <id> <state> "<说明>"
python3 __REPO_DIR__/scripts/kanban_update.py progress <id> "<当前动态>" "<计划清单>"
```

## 流计算工具

```bash
# 搜索流处理代码
rg "kafka\|flink\|stream\|consumer\|producer" __REPO_DIR__ --type py -i
find __REPO_DIR__ -name "*stream*" -o -name "*kafka*" -type f

# 消息队列状态
docker ps | grep kafka 2>/dev/null
curl -s http://localhost:8083/connectors 2>/dev/null

# 数据流监控
tail -f __REPO_DIR__/data/audit.log
```

## 环境信息

- 项目仓库：`__REPO_DIR__`
- Python：`python3`
