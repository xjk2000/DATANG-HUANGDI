"""Agent 模型"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class Agent(SQLModel, table=True):
    """Agent 数据模型"""

    __tablename__ = "agents"

    id: str = Field(primary_key=True, description="Agent ID，如 zhongshuling")
    name: str = Field(description="Agent 中文名称，如 中书令")
    group: str = Field(description="所属组织，如 中书省")
    role: str = Field(default="", description="职责描述")
    status: str = Field(default="unknown", description="状态: alive/idle/inactive/unknown")
    session_count: int = Field(default=0, description="会话数量")
    model: str = Field(default="", description="使用的 AI 模型")
    workspace: str = Field(default="", description="Workspace 路径")
    last_activity_at: Optional[datetime] = Field(default=None, description="最后活跃时间")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
