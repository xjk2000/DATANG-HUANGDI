#!/usr/bin/env python3
"""
朝堂消息协议 · DiWang Message Protocol

消息格式：
  【from:中书令  to:中书舍人】【任务id:T-042】【消息id:MSG-a1b2c3】请分析此旨意...

消息类型：
  edict     - 敕令下达
  request   - 请求协助 / 派发任务
  reply     - 正常回复 / 报告结果
  reject    - 封驳 / 驳回
  report    - 执行报告（含产出物）
  heartbeat - 心跳 / 巡检
"""

import json
import os
import uuid
from datetime import datetime, timezone

# ─── Agent 名称映射 ───────────────────────────────────────
AGENT_NAMES = {
    'emperor':         '皇帝',
    'zhongshuling':    '中书令',
    'zhongshu_sheren': '中书舍人',
    'shizhong':        '侍中侍郎',
    'jishizhong':      '给事中',
    'shangshuling':    '尚书令',
    'libu':            '吏部',
    'hubu':            '户部',
    'libu_protocol':   '礼部',
    'bingbu':          '兵部',
    'xingbu':          '刑部',
    'gongbu':          '工部',
    'jiangzuo':        '将作监',
    'shaofu':          '少府监',
    'junqi':           '军器监',
    'dushui':          '都水监',
    'sinong':          '司农监',
}

MSG_TYPES = ('edict', 'request', 'reply', 'reject', 'report', 'heartbeat')

MSG_TYPE_LABELS = {
    'edict':     '敕令',
    'request':   '请求',
    'reply':     '回复',
    'reject':    '封驳',
    'report':    '报告',
    'heartbeat': '心跳',
}


def now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def gen_msg_id():
    """生成短消息 ID：MSG-<8位hex>"""
    return f"MSG-{uuid.uuid4().hex[:8]}"


def agent_display_name(agent_id):
    """获取 Agent 显示名"""
    return AGENT_NAMES.get(agent_id, agent_id)


def create_message(from_agent, to_agent, task_id, msg_type, content,
                   ref_msg_id='', metadata=None):
    """
    创建一条朝堂消息。

    :param from_agent: 发送方 agent_id
    :param to_agent:   接收方 agent_id
    :param task_id:    关联任务 ID
    :param msg_type:   消息类型 (edict/request/reply/reject/report/heartbeat)
    :param content:    消息正文
    :param ref_msg_id: 引用消息 ID（回复/驳回时使用）
    :param metadata:   附加元数据 dict
    :return: 消息 dict
    """
    if msg_type not in MSG_TYPES:
        raise ValueError(f"未知消息类型: {msg_type} (可选: {MSG_TYPES})")

    msg_id = gen_msg_id()
    return {
        'msg_id':      msg_id,
        'msg_type':    msg_type,
        'from_agent':  from_agent,
        'to_agent':    to_agent,
        'task_id':     task_id,
        'ref_msg_id':  ref_msg_id,
        'content':     content,
        'metadata':    metadata or {},
        'status':      'pending',    # pending → delivered → read → processed
        'created_at':  now_iso(),
    }


def format_message(msg):
    """
    格式化消息为朝堂显示格式。

    输出：
      【from:中书令  to:中书舍人】【任务id:T-042】【消息id:MSG-a1b2c3】请分析此旨意...
    """
    from_name = agent_display_name(msg['from_agent'])
    to_name = agent_display_name(msg['to_agent'])
    type_label = MSG_TYPE_LABELS.get(msg['msg_type'], msg['msg_type'])

    header = (
        f"【from:{from_name}  to:{to_name}】"
        f"【任务id:{msg['task_id']}】"
        f"【消息id:{msg['msg_id']}】"
    )
    return f"{header}{msg['content']}"


def format_message_brief(msg):
    """格式化消息摘要（用于列表展示）"""
    from_name = agent_display_name(msg['from_agent'])
    to_name = agent_display_name(msg['to_agent'])
    type_label = MSG_TYPE_LABELS.get(msg['msg_type'], msg['msg_type'])
    content_preview = msg['content'][:40]
    if len(msg['content']) > 40:
        content_preview += '...'
    status_icon = {'pending': '📩', 'delivered': '📬', 'read': '📭', 'processed': '✅'}.get(
        msg.get('status', ''), '❓')

    return f"{status_icon} [{type_label}] {from_name}→{to_name} | {msg['task_id']} | {content_preview}"


def parse_message_header(text):
    """
    从格式化文本中解析消息头。

    输入：【from:中书令  to:中书舍人】【任务id:T-042】【消息id:MSG-a1b2c3】内容
    输出：{'from_display': '中书令', 'to_display': '中书舍人', 'task_id': 'T-042', 'msg_id': 'MSG-a1b2c3', 'content': '内容'}
    """
    import re
    pattern = r'【from:(.+?)\s+to:(.+?)】【任务id:(.+?)】【消息id:(.+?)】(.*)'
    m = re.match(pattern, text, re.DOTALL)
    if not m:
        return None
    return {
        'from_display': m.group(1).strip(),
        'to_display':   m.group(2).strip(),
        'task_id':      m.group(3).strip(),
        'msg_id':       m.group(4).strip(),
        'content':      m.group(5).strip(),
    }
