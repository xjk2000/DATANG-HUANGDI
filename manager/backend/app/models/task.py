"""敕令（任务）模型"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class Task(SQLModel, table=True):
    """敕令数据模型"""

    __tablename__ = "tasks"

    id: str = Field(primary_key=True, description="任务 ID")
    title: str = Field(description="任务标题")
    state: str = Field(default="Imperial", description="当前状态")
    org: str = Field(default="", description="所属部门")
    official: str = Field(default="", description="负责人 Agent ID")
    official_name: str = Field(default="", description="负责人名称")
    content: str = Field(default="", description="任务内容摘要")
    source: str = Field(default="manual", description="来源: manual/openclaw_session")
    session_id: Optional[str] = Field(default=None, description="关联的 OpenClaw session ID")
    message_count: int = Field(default=0, description="消息数量")
    output: str = Field(default="", description="执行结果")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
