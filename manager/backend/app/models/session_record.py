"""会话记录模型"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class SessionRecord(SQLModel, table=True):
    """OpenClaw 会话记录"""

    __tablename__ = "session_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True, description="OpenClaw session ID")
    agent_id: str = Field(index=True, description="Agent ID")
    title: str = Field(default="", description="会话标题（第一条消息摘要）")
    message_count: int = Field(default=0, description="消息数量")
    file_path: str = Field(default="", description="JSONL 文件路径")
    file_mtime: float = Field(default=0.0, description="文件最后修改时间")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
