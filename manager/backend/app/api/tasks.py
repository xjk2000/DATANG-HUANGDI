"""敕令（任务）管理 API"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.database import get_session
from app.models.audit_log import AuditLog
from app.models.task import Task

router = APIRouter(prefix="/tasks", tags=["tasks"])

# 合法状态转换
VALID_TRANSITIONS = {
    "Imperial":       ["ZhongshuDraft", "Cancelled"],
    "ZhongshuDraft":  ["ZhongshuReview", "MenxiaReview", "Cancelled"],
    "ZhongshuReview": ["MenxiaReview", "ZhongshuDraft", "Cancelled"],
    "MenxiaReview":   ["Approved", "Rejected", "ZhongshuDraft", "Cancelled"],
    "Rejected":       ["ZhongshuDraft", "Cancelled"],
    "Approved":       ["Dispatching", "Cancelled"],
    "Dispatching":    ["Executing", "Cancelled"],
    "Executing":      ["Review", "Done", "Blocked", "Cancelled"],
    "Review":         ["Done", "Executing", "Blocked", "Cancelled"],
    "Done":           [],
    "Cancelled":      [],
    "Blocked":        ["Executing", "Cancelled"],
}

STATE_LABELS = {
    "Imperial": "皇帝下旨",
    "ZhongshuDraft": "中书起草",
    "ZhongshuReview": "中书内审",
    "MenxiaReview": "门下审议",
    "Rejected": "门下封驳",
    "Approved": "准奏通过",
    "Dispatching": "尚书派发",
    "Executing": "执行中",
    "Review": "待审查",
    "Done": "已完成",
    "Cancelled": "已取消",
    "Blocked": "阻塞",
}


class TaskCreate(BaseModel):
    """创建任务请求"""
    id: str
    title: str
    state: str = "Imperial"
    org: str = ""
    official: str = ""
    content: str = ""


class TaskStateChange(BaseModel):
    """状态变更请求"""
    state: str
    detail: str = ""


class TaskDone(BaseModel):
    """完成任务请求"""
    output: str = ""
    summary: str = ""


@router.get("", response_model=list[Task])
async def list_tasks(
    state: Optional[str] = Query(None),
    org: Optional[str] = Query(None),
    official: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """获取敕令列表"""
    query = select(Task)
    if state:
        query = query.where(Task.state == state)
    if org:
        query = query.where(Task.org == org)
    if official:
        query = query.where(Task.official == official)
    query = query.order_by(Task.updated_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/summary")
async def task_summary(session: AsyncSession = Depends(get_session)):
    """获取任务统计摘要"""
    result = await session.execute(
        select(Task.state, func.count(Task.id)).group_by(Task.state)
    )
    state_counts = {row[0]: row[1] for row in result.all()}

    result = await session.execute(
        select(Task.org, func.count(Task.id)).group_by(Task.org)
    )
    org_counts = {row[0]: row[1] for row in result.all()}

    total = sum(state_counts.values())
    active = state_counts.get("Executing", 0) + state_counts.get("Dispatching", 0)
    done = state_counts.get("Done", 0)

    return {
        "total": total,
        "active": active,
        "done": done,
        "stateCounts": state_counts,
        "stateLabels": STATE_LABELS,
        "orgCounts": org_counts,
    }


@router.get("/states")
async def get_states():
    """获取所有状态定义"""
    return {"states": STATE_LABELS, "transitions": VALID_TRANSITIONS}


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str, session: AsyncSession = Depends(get_session)):
    """获取单个敕令详情"""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return task


@router.post("", response_model=Task)
async def create_task(data: TaskCreate, session: AsyncSession = Depends(get_session)):
    """创建新敕令"""
    existing = await session.get(Task, data.id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Task already exists: {data.id}")

    if data.state not in STATE_LABELS:
        raise HTTPException(status_code=400, detail=f"Invalid state: {data.state}")

    now = datetime.now(timezone.utc)
    task = Task(
        id=data.id,
        title=data.title,
        state=data.state,
        org=data.org,
        official=data.official,
        content=data.content,
        created_at=now,
        updated_at=now,
    )
    session.add(task)

    audit = AuditLog(
        action="create",
        task_id=data.id,
        detail=f"创建敕令: {data.title}",
        new_state=data.state,
        created_at=now,
    )
    session.add(audit)

    await session.commit()
    await session.refresh(task)
    return task


@router.put("/{task_id}/state", response_model=Task)
async def change_task_state(
    task_id: str,
    data: TaskStateChange,
    session: AsyncSession = Depends(get_session),
):
    """变更敕令状态"""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    if data.state not in STATE_LABELS:
        raise HTTPException(status_code=400, detail=f"Invalid state: {data.state}")

    if data.state not in VALID_TRANSITIONS.get(task.state, []):
        raise HTTPException(
            status_code=400,
            detail=f"非法状态跳转: {task.state} → {data.state}",
        )

    now = datetime.now(timezone.utc)
    old_state = task.state
    task.state = data.state
    task.updated_at = now

    audit = AuditLog(
        action="state_change",
        task_id=task_id,
        detail=data.detail or f"状态变更: {STATE_LABELS.get(old_state, old_state)} → {STATE_LABELS.get(data.state, data.state)}",
        old_state=old_state,
        new_state=data.state,
        created_at=now,
    )
    session.add(audit)

    await session.commit()
    await session.refresh(task)
    return task


@router.put("/{task_id}/done", response_model=Task)
async def complete_task(
    task_id: str,
    data: TaskDone,
    session: AsyncSession = Depends(get_session),
):
    """完成敕令"""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    if task.state == "Done":
        raise HTTPException(status_code=409, detail=f"敕令已完成，不可重复操作: {task_id}")

    if task.state not in ("Executing", "Review", "Dispatching"):
        valid = VALID_TRANSITIONS.get(task.state, [])
        if "Done" not in valid:
            raise HTTPException(
                status_code=400,
                detail=f"非法状态跳转: {task.state} → Done",
            )

    now = datetime.now(timezone.utc)
    old_state = task.state
    task.state = "Done"
    task.output = data.output
    task.updated_at = now

    audit = AuditLog(
        action="done",
        task_id=task_id,
        detail=data.summary or "任务完成",
        old_state=old_state,
        new_state="Done",
        created_at=now,
    )
    session.add(audit)

    await session.commit()
    await session.refresh(task)
    return task
