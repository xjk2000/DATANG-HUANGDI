# TOOLS.md - 给事中工具配置

## 终端搜索

```bash
# 代码验证
rg "函数名或类名" __REPO_DIR__ --type py
find __REPO_DIR__ -name "文件名" -type f

# 依赖检查
cat __REPO_DIR__/requirements.txt 2>/dev/null

# 语法验证
python3 -c "import ast; ast.parse(open('文件路径').read())"
```

## 数据文件

- 任务数据：`__REPO_DIR__/data/tasks.json`

## 环境信息

- 项目仓库：`__REPO_DIR__`
- Python：`python3`
