# TOOLS.md - 兵部工具配置

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

## SRE 运维工具

```bash
# 容器管理
docker ps -a
docker logs <container> --tail 50

# K8s 管理
kubectl get pods -A
kubectl get svc -A
kubectl describe pod <name>

# 网络诊断
ss -ltnp | head -20
curl -s http://127.0.0.1:7891/api/health

# CI/CD
find __REPO_DIR__ -name "Dockerfile" -o -name "docker-compose*" -type f

# 系统资源
df -h
free -h 2>/dev/null || vm_stat
top -bn1 | head -20 2>/dev/null
```

## 环境信息

- 项目仓库：`__REPO_DIR__`
- 看板服务：`http://127.0.0.1:7891`
- Python：`python3`
