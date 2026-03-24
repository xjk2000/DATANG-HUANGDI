#!/usr/bin/env python3
"""
朝堂消息总线 · Message Bus

所有跨 Agent 通信的唯一入口。
职责：校验路由 → 写入收件箱 → 追加会话线程 → 记录审计日志。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from session.message import (
    create_message, format_message, agent_display_name,
    MSG_TYPE_LABELS, now_iso,
)
from session.router import validate_route, RoutingError
from session.session_store import (
    save_to_inbox, append_to_thread, session_audit_log,
    update_message_status, get_message, get_inbox,
)


class MessageBus:
    """帝王系统消息总线"""

    def send(self, from_agent, to_agent, task_id, msg_type, content,
             ref_msg_id='', metadata=None):
        """
        发送消息（校验 → 路由 → 入队 → 记录）。

        :return: 消息 dict
        :raises RoutingError: 路由非法时抛出
        """
        # 1. 校验路由
        ok, err = validate_route(from_agent, to_agent)
        if not ok:
            session_audit_log(f"ROUTE_DENIED {from_agent} → {to_agent} | {err}")
            raise RoutingError(err)

        # 2. 创建消息
        msg = create_message(
            from_agent=from_agent,
            to_agent=to_agent,
            task_id=task_id,
            msg_type=msg_type,
            content=content,
            ref_msg_id=ref_msg_id,
            metadata=metadata,
        )

        # 3. 写入收件箱
        save_to_inbox(to_agent, msg)

        # 4. 追加到会话线程
        append_to_thread(task_id, msg)

        # 5. 审计日志
        from_name = agent_display_name(from_agent)
        to_name = agent_display_name(to_agent)
        type_label = MSG_TYPE_LABELS.get(msg_type, msg_type)
        session_audit_log(
            f"SEND {msg['msg_id']} | [{type_label}] {from_name}→{to_name} | "
            f"任务:{task_id} | {content[:60]}"
        )

        return msg

    def reply(self, from_agent, ref_msg_id, content, metadata=None):
        """
        回复一条消息。自动查找原消息的发送方作为目标。

        :return: 新消息 dict
        :raises ValueError: 原消息不存在
        """
        # 查找原消息：遍历 from_agent 的收件箱
        original = get_message(from_agent, ref_msg_id)
        if original is None:
            raise ValueError(f"未找到消息: {ref_msg_id}（在 {from_agent} 收件箱中）")

        return self.send(
            from_agent=from_agent,
            to_agent=original['from_agent'],
            task_id=original['task_id'],
            msg_type='reply',
            content=content,
            ref_msg_id=ref_msg_id,
            metadata=metadata,
        )

    def reject(self, from_agent, ref_msg_id, reason, metadata=None):
        """
        封驳一条消息（门下省专用）。

        :return: 封驳消息 dict
        """
        original = get_message(from_agent, ref_msg_id)
        if original is None:
            raise ValueError(f"未找到消息: {ref_msg_id}（在 {from_agent} 收件箱中）")

        return self.send(
            from_agent=from_agent,
            to_agent=original['from_agent'],
            task_id=original['task_id'],
            msg_type='reject',
            content=reason,
            ref_msg_id=ref_msg_id,
            metadata=metadata,
        )

    def ack(self, agent_id, msg_id):
        """确认消息已处理"""
        ok = update_message_status(agent_id, msg_id, 'processed')
        if ok:
            session_audit_log(f"ACK {msg_id} | {agent_display_name(agent_id)} 已处理")
        return ok

    def mark_read(self, agent_id, msg_id):
        """标记消息为已读"""
        return update_message_status(agent_id, msg_id, 'read')

    def inbox(self, agent_id, status_filter=None):
        """获取 Agent 收件箱"""
        return get_inbox(agent_id, status_filter)


# 全局单例
bus = MessageBus()
