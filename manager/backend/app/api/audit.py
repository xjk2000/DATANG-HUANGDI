"""审计日志 API"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.database import get_session
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditLog])
async def list_audit_logs(
    task_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """获取审计日志"""
    query = select(AuditLog)
    if task_id:
        query = query.where(AuditLog.task_id == task_id)
    if agent_id:
        query = query.where(AuditLog.agent_id == agent_id)
    if action:
        query = query.where(AuditLog.action == action)
    query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/summary")
async def audit_summary(session: AsyncSession = Depends(get_session)):
    """审计日志统计"""
    result = await session.execute(
        select(AuditLog.action, func.count(AuditLog.id)).group_by(AuditLog.action)
    )
    action_counts = {row[0]: row[1] for row in result.all()}

    result = await session.execute(select(func.count(AuditLog.id)))
    total = result.scalar() or 0

    return {
        "total": total,
        "action_counts": action_counts,
    }
