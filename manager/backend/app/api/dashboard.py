"""Dashboard 指标 API"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.database import get_session
from app.models.agent import Agent
from app.models.audit_log import AuditLog
from app.models.session_record import SessionRecord
from app.models.task import Task

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics")
async def dashboard_metrics(session: AsyncSession = Depends(get_session)):
    """Dashboard 总览指标"""
    # Agent 统计
    result = await session.execute(select(func.count(Agent.id)))
    total_agents = result.scalar() or 0

    result = await session.execute(
        select(func.count(Agent.id)).where(Agent.status == "alive")
    )
    online_agents = result.scalar() or 0

    # 任务统计
    result = await session.execute(
        select(Task.state, func.count(Task.id)).group_by(Task.state)
    )
    state_counts = {row[0]: row[1] for row in result.all()}
    total_tasks = sum(state_counts.values())
    active_tasks = state_counts.get("Executing", 0) + state_counts.get("Dispatching", 0)
    done_tasks = state_counts.get("Done", 0)
    blocked_tasks = state_counts.get("Blocked", 0)
    review_tasks = state_counts.get("Review", 0) + state_counts.get("MenxiaReview", 0)

    # 会话统计
    result = await session.execute(select(func.count(SessionRecord.id)))
    total_sessions = result.scalar() or 0

    result = await session.execute(select(func.sum(SessionRecord.message_count)))
    total_messages = result.scalar() or 0

    # 审计日志统计
    result = await session.execute(select(func.count(AuditLog.id)))
    total_audit_logs = result.scalar() or 0

    # 部门统计
    result = await session.execute(
        select(Task.org, func.count(Task.id)).group_by(Task.org)
    )
    org_counts = {row[0]: row[1] for row in result.all()}

    # 完成率
    completion_rate = round(done_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0.0

    return {
        "agents": {
            "total": total_agents,
            "online": online_agents,
        },
        "tasks": {
            "total": total_tasks,
            "active": active_tasks,
            "done": done_tasks,
            "blocked": blocked_tasks,
            "review": review_tasks,
            "completion_rate": completion_rate,
            "state_counts": state_counts,
            "org_counts": org_counts,
        },
        "sessions": {
            "total": total_sessions,
            "total_messages": total_messages,
        },
        "audit": {
            "total": total_audit_logs,
        },
    }
