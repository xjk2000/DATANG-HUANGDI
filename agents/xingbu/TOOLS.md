# TOOLS.md - 刑部工具配置

## 任务回报（必用！完成后立即调用）

```bash
python3 __REPO_DIR__/scripts/task_dispatch.py report <敕令ID> <子任务序号> "<执行结果>" "<产出物>"
```

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

## 功能验证 — 日志模式提取（第一步，为户部提供关键词）

```bash
# 从被监控项目代码中提取实际日志模式
# 项目路径来自 __REPO_DIR__/data/diwang.json 中的 project_dir
python3 __REPO_DIR__/scripts/sls_query.py analyze-logs <功能关键词>

# 示例
python3 __REPO_DIR__/scripts/sls_query.py analyze-logs UserLogin
python3 __REPO_DIR__/scripts/sls_query.py analyze-logs OrderCreate

# 覆盖项目路径（更新 diwang.json 中的 project_dir 不方便时）
python3 __REPO_DIR__/scripts/sls_query.py analyze-logs UserLogin --project-dir /path/to/project
```

**输出示例：**
```
🔍 代码日志分析: [UserLogin]
   项目路径: /path/to/your/project
────────────────────────────────────────────────────────────────
📄 找到 3 条日志语句:
  [1] [java] .../UserLoginService.java:45
       log.info("用户登录成功: userId={}", userId);
       → 日志内容: "用户登录成功"
────────────────────────────────────────────────────────────────
💡 推荐 SLS 查询关键词（直接传给户部的查询语句）:
   "用户登录成功"

📋 示例（生产环境，最近 1 小时）:
   python3 sls_query.py production \
     "$(date -d -1hour +"%Y-%m-%d %H:%M:%S")" \
     "$(date +"%Y-%m-%d %H:%M:%S")" \
     '"用户登录成功" OR "登录失败"'
```

## 功能验证 — 代码搜索

> 项目可能是 Java / Python / TypeScript 等任意语言，不加 `--type` 限制或按实际语言选择。
> 项目路径在 `__REPO_DIR__/data/diwang.json` 中的 `project_dir` 字段。

```bash
# ① 先判断项目语言
find __REPO_DIR__ -name "*.java" | head -3   # Java
find __REPO_DIR__ -name "*.py"  | head -3   # Python
find __REPO_DIR__ -name "*.ts"  | head -3   # TypeScript
find __REPO_DIR__ -name "pom.xml" -o -name "build.gradle" | head -3   # Maven/Gradle

# ② 搜索功能关键词所在文件
rg "<功能关键词>" __REPO_DIR__ -l
rg "<功能关键词>" __REPO_DIR__ -l --type java   # Java 项目
rg "<功能关键词>" __REPO_DIR__ -l --type py    # Python 项目

# ③ 搜索方法/类定义
# Java
rg "(public|private|protected).*<功能关键词>" __REPO_DIR__ --type java -n
rg "class <功能关键词>" __REPO_DIR__ --type java -n
# Python
rg "def .*<功能关键词>" __REPO_DIR__ --type py -n
rg "class .*<功能关键词>" __REPO_DIR__ --type py -n

# ④ 搜索 API 路由入口
# Java (Spring)
rg "@GetMapping\|@PostMapping\|@RequestMapping\|@RestController" __REPO_DIR__ --type java -n
rg "@(Get|Post|Put|Delete|Patch)Mapping.*<功能关键词>" __REPO_DIR__ --type java -n
# Python (FastAPI/Flask)
rg "@router\.(get|post|put|delete)\|@app\.(get|post)" __REPO_DIR__ --type py -n

# ⑤ 查看异常处理
# Java
rg "catch\s*\(|throws\s+|throw\s+new" <具体文件> -n
# Python
rg "try:|except |raise " <具体文件> -n

# ⑥ 查看测试代码
# Java
find __REPO_DIR__ -path "*/test*" -name "*<功能关键词>*Test*.java"
rg "<功能关键词>" __REPO_DIR__ --type java -g "*Test*" -n
# Python
rg "<功能关键词>" __REPO_DIR__/tests --type py -n

# ⑦ 查看代码上下文（前后 5 行）
rg "<具体方法名>" __REPO_DIR__ -A 5 -B 5
```

## 环境信息

- 项目仓库：`__REPO_DIR__`
- 测试目录：`__REPO_DIR__/tests/`
- 配置文件：`__REPO_DIR__/data/diwang.json`（`project_dir` + SLS 参数）
- Python：`python3`
