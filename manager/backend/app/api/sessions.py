"""会话记录 API"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.database import get_session
from app.models.session_record import SessionRecord

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionRecord])
async def list_sessions(
    agent_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """获取会话列表"""
    query = select(SessionRecord)
    if agent_id:
        query = query.where(SessionRecord.agent_id == agent_id)
    query = query.order_by(SessionRecord.updated_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/summary")
async def session_summary(session: AsyncSession = Depends(get_session)):
    """获取会话统计"""
    result = await session.execute(
        select(
            SessionRecord.agent_id,
            func.count(SessionRecord.id),
            func.sum(SessionRecord.message_count),
        ).group_by(SessionRecord.agent_id)
    )
    agent_stats = {}
    for row in result.all():
        agent_stats[row[0]] = {
            "session_count": row[1],
            "message_count": row[2] or 0,
        }

    total_sessions = sum(s["session_count"] for s in agent_stats.values())
    total_messages = sum(s["message_count"] for s in agent_stats.values())

    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "agent_stats": agent_stats,
    }


@router.get("/{session_id}", response_model=SessionRecord)
async def get_session_record(
    session_id: str,
    session: AsyncSession = Depends(get_session),
):
    """获取单条会话详情"""
    result = await session.execute(
        select(SessionRecord).where(SessionRecord.session_id == session_id)
    )
    record = result.scalars().first()
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    return record
