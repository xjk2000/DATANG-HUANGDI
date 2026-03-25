"""审计日志模型"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class AuditLog(SQLModel, table=True):
    """审计日志"""

    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    action: str = Field(description="操作类型: create/state_change/flow/done/cancel")
    task_id: str = Field(default="", index=True, description="关联任务 ID")
    agent_id: str = Field(default="", index=True, description="操作者 Agent ID")
    detail: str = Field(default="", description="操作详情")
    old_state: str = Field(default="", description="原状态")
    new_state: str = Field(default="", description="新状态")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
