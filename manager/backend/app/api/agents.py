"""Agent 管理 API"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.models.agent import Agent

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[Agent])
async def list_agents(session: AsyncSession = Depends(get_session)):
    """获取所有 Agent 列表"""
    result = await session.execute(select(Agent).order_by(Agent.group, Agent.name))
    return result.scalars().all()


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str, session: AsyncSession = Depends(get_session)):
    """获取单个 Agent 详情"""
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return agent


@router.get("/group/{group_name}", response_model=list[Agent])
async def list_agents_by_group(group_name: str, session: AsyncSession = Depends(get_session)):
    """按部门获取 Agent"""
    result = await session.execute(select(Agent).where(Agent.group == group_name))
    return result.scalars().all()
