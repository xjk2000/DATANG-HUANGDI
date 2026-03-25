# 帝王系统 · 管理后台

参考 [openclaw-mission-control](https://github.com/abhi1693/openclaw-mission-control) 和 [Star-Office-UI](https://github.com/ringhyacinth/Star-Office-UI) 设计实现。

## 技术栈

**后端**：FastAPI + SQLModel + SQLite + aiosqlite
**前端**：Next.js 14 + React 18 + TailwindCSS + TanStack Query + Recharts

## 功能

- **Dashboard 总览** — 在线官员、执行中敕令、完成率、会话数等指标卡片
- **官员总览** — 三省六部五监分组展示，状态/会话/模型/最后活跃时间
- **敕令看板** — 12 种状态过滤、状态流转、任务列表
- **会话记录** — OpenClaw session 自动同步，消息统计
- **审计日志** — 所有状态变更的完整记录
- **实时同步** — 后台每 15 秒自动从 OpenClaw 同步 Agent 状态和会话

## 快速开始

### 本地开发

```bash
# 1. 启动后端
cd manager/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 7900

# 2. 启动前端
cd manager/frontend
npm install
npm run dev
```

- 后端 API: http://localhost:7900
- 前端界面: http://localhost:3000
- API 文档: http://localhost:7900/docs

### Docker 部署

```bash
cd manager
docker compose up -d
```

## 目录结构

```
manager/
  backend/
    app/
      api/          API 路由（agents, tasks, sessions, audit, dashboard）
      core/         配置和数据库
      models/       数据模型（Agent, Task, SessionRecord, AuditLog）
      services/     业务逻辑（OpenClaw 同步服务）
      main.py       FastAPI 入口
    requirements.txt
    Dockerfile
  frontend/
    src/
      app/          Next.js 页面（Dashboard, Agents, Tasks, Sessions, Audit）
      components/   共享组件（Sidebar, Providers）
      lib/          API 客户端和常量
    package.json
    Dockerfile
  docker-compose.yml
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/dashboard/metrics` | Dashboard 总览指标 |
| GET | `/api/v1/agents` | Agent 列表 |
| GET | `/api/v1/agents/{id}` | Agent 详情 |
| GET | `/api/v1/tasks` | 敕令列表（支持 state/org 过滤） |
| GET | `/api/v1/tasks/summary` | 敕令统计 |
| POST | `/api/v1/tasks` | 创建敕令 |
| PUT | `/api/v1/tasks/{id}/state` | 变更敕令状态 |
| GET | `/api/v1/sessions` | 会话列表 |
| GET | `/api/v1/audit` | 审计日志 |
| GET | `/api/v1/sync` | 手动触发同步 |
| GET | `/health` | 健康检查 |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DIWANG_REPO_DIR` | 项目根目录 | 帝王系统项目路径 |
| `DIWANG_OPENCLAW_HOME` | `~/.openclaw` | OpenClaw 安装路径 |
| `DIWANG_DATABASE_URL` | `sqlite+aiosqlite:///data/diwang.db` | 数据库连接 |
| `DIWANG_PORT` | `7900` | 后端端口 |
| `DIWANG_CORS_ORIGINS` | `http://localhost:3000` | CORS 允许的来源 |
| `DIWANG_SYNC_INTERVAL_SECONDS` | `15` | 数据同步间隔（秒） |
