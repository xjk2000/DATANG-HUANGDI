"""OpenClaw 数据同步服务

从 OpenClaw 运行时读取 Agent 状态、会话记录等，同步到数据库。
"""

import glob
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.models.agent import Agent
from app.models.session_record import SessionRecord
from app.models.task import Task

# Agent 元数据
AGENT_META = {
    "zhongshuling": {"name": "中书令", "group": "中书省", "role": "取旨起草"},
    "zhongshu_sheren": {"name": "中书舍人", "group": "中书省", "role": "记录辅析"},
    "shizhong": {"name": "侍中侍郎", "group": "门下省", "role": "审议封驳"},
    "jishizhong": {"name": "给事中", "group": "门下省", "role": "逐条审查"},
    "shangshuling": {"name": "尚书令", "group": "尚书省", "role": "调度派发"},
    "libu": {"name": "吏部", "group": "六部", "role": "Agent 生命周期管理"},
    "hubu": {"name": "户部", "group": "六部", "role": "数据库与报表"},
    "libu_protocol": {"name": "礼部", "group": "六部", "role": "API 协议规范"},
    "bingbu": {"name": "兵部", "group": "六部", "role": "CI/CD 与运维"},
    "xingbu": {"name": "刑部", "group": "六部", "role": "测试与审计"},
    "gongbu": {"name": "工部", "group": "六部", "role": "基础设施"},
    "jiangzuo": {"name": "将作监", "group": "五监", "role": "核心业务开发"},
    "shaofu": {"name": "少府监", "group": "五监", "role": "前端与交互"},
    "junqi": {"name": "军器监", "group": "五监", "role": "安全工具"},
    "dushui": {"name": "都水监", "group": "五监", "role": "流计算"},
    "sinong": {"name": "司农监", "group": "五监", "role": "算法与数据"},
}


def _get_sessions_dir(agent_id: str) -> str:
    """获取 Agent 的 session transcripts 目录"""
    return os.path.join(settings.OPENCLAW_HOME, "sessions", "transcripts", agent_id)


def _get_last_activity(agent_id: str):
    """获取 Agent 最后活跃时间"""
    sessions_dir = _get_sessions_dir(agent_id)
    if not os.path.isdir(sessions_dir):
        return None

    latest_mtime = 0
    for f in glob.glob(os.path.join(sessions_dir, "*.jsonl")):
        mtime = os.path.getmtime(f)
        if mtime > latest_mtime:
            latest_mtime = mtime

    if latest_mtime == 0:
        return None
    return datetime.fromtimestamp(latest_mtime, tz=timezone.utc)


def _check_agent_status(agent_id: str) -> str:
    """检查 Agent 活跃状态"""
    last = _get_last_activity(agent_id)
    if not last:
        return "unknown"
    delta = (datetime.now(timezone.utc) - last).total_seconds()
    if delta < 300:
        return "alive"
    elif delta < 1800:
        return "idle"
    else:
        return "inactive"


def _count_sessions(agent_id: str) -> int:
    """统计 Agent 的会话数"""
    sessions_dir = _get_sessions_dir(agent_id)
    if not os.path.isdir(sessions_dir):
        return 0
    return len(glob.glob(os.path.join(sessions_dir, "*.jsonl")))


def _get_agent_model(agent_id: str) -> str:
    """获取 Agent 使用的模型"""
    oc_cfg_path = os.path.join(settings.OPENCLAW_HOME, "openclaw.json")
    if not os.path.exists(oc_cfg_path):
        return ""
    try:
        with open(oc_cfg_path, "r", encoding="utf-8") as f:
            oc_cfg = json.load(f)
        agents_list = oc_cfg.get("agents", {}).get("list", [])
        for agent in agents_list:
            if agent.get("id") == agent_id:
                model = agent.get("model", {})
                if isinstance(model, str):
                    return model
                elif isinstance(model, dict):
                    return model.get("primary", "")
                return ""
    except Exception:
        pass
    return ""


async def sync_agents(session: AsyncSession):
    """同步所有 Agent 状态到数据库"""
    now = datetime.now(timezone.utc)

    for agent_id, meta in AGENT_META.items():
        status = _check_agent_status(agent_id)
        session_count = _count_sessions(agent_id)
        last_activity = _get_last_activity(agent_id)
        model = _get_agent_model(agent_id)
        workspace = os.path.join(settings.OPENCLAW_HOME, f"workspace-{agent_id}")

        existing = await session.get(Agent, agent_id)
        if existing:
            existing.status = status
            existing.session_count = session_count
            existing.last_activity_at = last_activity
            existing.model = model
            existing.workspace = workspace
            existing.updated_at = now
        else:
            agent = Agent(
                id=agent_id,
                name=meta["name"],
                group=meta["group"],
                role=meta["role"],
                status=status,
                session_count=session_count,
                model=model,
                workspace=workspace,
                last_activity_at=last_activity,
                created_at=now,
                updated_at=now,
            )
            session.add(agent)

    await session.commit()


def _parse_session_file(filepath: str):
    """解析 session JSONL 文件"""
    messages = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception:
        return None

    if not messages:
        return None

    user_messages = [m for m in messages if m.get("role") == "user"]
    if not user_messages:
        return None

    first_msg = user_messages[0]
    content = first_msg.get("content", "")
    if isinstance(content, list):
        text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
        content = "\n".join(text_parts)

    title_line = content.split("\n")[0] if "\n" in content else content
    title = title_line[:80] + ("..." if len(title_line) > 80 else "")

    return {
        "title": title,
        "message_count": len(messages),
    }


async def sync_sessions(session: AsyncSession):
    """同步 OpenClaw 会话到数据库"""
    now = datetime.now(timezone.utc)
    sessions_base = os.path.join(settings.OPENCLAW_HOME, "sessions", "transcripts")
    if not os.path.isdir(sessions_base):
        return

    created = 0
    updated = 0

    for agent_id in AGENT_META:
        agent_dir = os.path.join(sessions_base, agent_id)
        if not os.path.isdir(agent_dir):
            continue

        for filepath in glob.glob(os.path.join(agent_dir, "*.jsonl")):
            session_id = os.path.basename(filepath).replace(".jsonl", "")
            mtime = os.path.getmtime(filepath)

            # 查找是否已存在
            result = await session.execute(
                select(SessionRecord).where(SessionRecord.session_id == session_id)
            )
            existing = result.scalars().first()

            if existing and existing.file_mtime == mtime:
                continue  # 未修改，跳过

            parsed = _parse_session_file(filepath)
            if not parsed:
                continue

            if existing:
                existing.title = parsed["title"]
                existing.message_count = parsed["message_count"]
                existing.file_mtime = mtime
                existing.updated_at = now
                updated += 1
            else:
                record = SessionRecord(
                    session_id=session_id,
                    agent_id=agent_id,
                    title=parsed["title"],
                    message_count=parsed["message_count"],
                    file_path=filepath,
                    file_mtime=mtime,
                    created_at=now,
                    updated_at=now,
                )
                session.add(record)
                created += 1

    await session.commit()
    return {"created": created, "updated": updated}


async def sync_sessions_to_tasks(session: AsyncSession):
    """将新会话同步为看板任务"""
    now = datetime.now(timezone.utc)
    created = 0

    result = await session.execute(select(SessionRecord))
    all_sessions = result.scalars().all()

    for record in all_sessions:
        task_id = f"SESSION-{record.agent_id}-{record.session_id[:8]}"
        existing_task = await session.get(Task, task_id)
        if existing_task:
            existing_task.message_count = record.message_count
            existing_task.updated_at = now
            continue

        meta = AGENT_META.get(record.agent_id, {})
        task = Task(
            id=task_id,
            title=record.title or "未命名会话",
            state="Executing",
            org=meta.get("group", ""),
            official=record.agent_id,
            official_name=meta.get("name", record.agent_id),
            content=record.title[:200] if record.title else "",
            source="openclaw_session",
            session_id=record.session_id,
            message_count=record.message_count,
            created_at=record.created_at,
            updated_at=now,
        )
        session.add(task)
        created += 1

    await session.commit()
    return {"created": created}


async def run_full_sync(session: AsyncSession):
    """执行完整同步"""
    await sync_agents(session)
    sessions_result = await sync_sessions(session)
    tasks_result = await sync_sessions_to_tasks(session)
    return {
        "agents": "synced",
        "sessions": sessions_result,
        "tasks": tasks_result,
    }
