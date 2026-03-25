"""应用配置"""

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """帝王系统管理后台配置"""

    # 项目路径
    REPO_DIR: str = str(Path(__file__).resolve().parents[4])
    OPENCLAW_HOME: str = os.path.join(str(Path.home()), ".openclaw")

    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///data/diwang.db"

    # 服务
    HOST: str = "0.0.0.0"
    PORT: int = 7900
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:7900"

    # 同步配置
    SYNC_INTERVAL_SECONDS: int = 15

    # API
    API_V1_PREFIX: str = "/api/v1"

    class Config:
        env_prefix = "DIWANG_"
        env_file = ".env"

    @property
    def data_dir(self) -> str:
        return os.path.join(self.REPO_DIR, "data")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
