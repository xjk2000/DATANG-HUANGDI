# TOOLS.md - 少府监工具配置

## 任务回报（必用！完成后立即调用）

```bash
python3 __REPO_DIR__/scripts/task_dispatch.py report <敕令ID> <子任务序号> "<执行结果>" "<产出物>"
```

## 看板 CLI

```bash
python3 __REPO_DIR__/scripts/kanban_update.py state <id> <state> "<说明>"
python3 __REPO_DIR__/scripts/kanban_update.py progress <id> "<当前动态>" "<计划清单>"
```

## 前端开发工具

```bash
# 搜索前端文件
find __REPO_DIR__ -name "*.html" -o -name "*.css" -o -name "*.js" -type f
rg "function \|const \|class " __REPO_DIR__/dashboard/

# 端口检查
lsof -i :7891 2>/dev/null || ss -ltnp | grep 7891

# Node.js 依赖
cat __REPO_DIR__/package.json 2>/dev/null | python3 -m json.tool
```

## 环境信息

- 项目仓库：`__REPO_DIR__`
- 看板前端：`__REPO_DIR__/dashboard/index.html`
- 看板服务：`http://127.0.0.1:7891`
- Python：`python3`
