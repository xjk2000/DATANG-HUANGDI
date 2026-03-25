"""数据库初始化"""

import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings

# 确保 data 目录存在
os.makedirs(settings.data_dir, exist_ok=True)

# 构建数据库 URL（相对路径转绝对路径）
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite+aiosqlite:///") and not db_url.startswith("sqlite+aiosqlite:////"):
    relative_path = db_url.replace("sqlite+aiosqlite:///", "")
    absolute_path = os.path.join(settings.REPO_DIR, relative_path)
    os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
    db_url = f"sqlite+aiosqlite:///{absolute_path}"

engine = create_async_engine(db_url, echo=False)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """创建所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    """获取数据库 session（FastAPI 依赖注入用）"""
    async with async_session() as session:
        yield session
