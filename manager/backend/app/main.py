"""帝王系统管理后台 · FastAPI 入口"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agents import router as agents_router
from app.api.audit import router as audit_router
from app.api.dashboard import router as dashboard_router
from app.api.sessions import router as sessions_router
from app.api.tasks import router as tasks_router
from app.core.config import settings
from app.core.database import async_session, init_db
from app.services.sync_service import run_full_sync


async def _background_sync():
    """后台定时同步 OpenClaw 数据"""
    while True:
        try:
            async with async_session() as session:
                await run_full_sync(session)
        except Exception as e:
            print(f"[sync] 同步失败: {e}")
        await asyncio.sleep(settings.SYNC_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()

    # 首次同步
    try:
        async with async_session() as session:
            result = await run_full_sync(session)
            print(f"[sync] 初始同步完成: {result}")
    except Exception as e:
        print(f"[sync] 初始同步失败: {e}")

    # 启动后台同步任务
    sync_task = asyncio.create_task(_background_sync())

    yield

    # 关闭时取消后台任务
    sync_task.cancel()
    try:
        await sync_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="帝王系统管理后台",
    description="大唐皇帝 · 三省六部五监 · 17 Agent 管理系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)
app.include_router(agents_router, prefix=settings.API_V1_PREFIX)
app.include_router(tasks_router, prefix=settings.API_V1_PREFIX)
app.include_router(sessions_router, prefix=settings.API_V1_PREFIX)
app.include_router(audit_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "diwang-manager"}


@app.get(f"{settings.API_V1_PREFIX}/sync")
async def trigger_sync():
    """手动触发同步"""
    async with async_session() as session:
        result = await run_full_sync(session)
    return {"status": "ok", "result": result}
