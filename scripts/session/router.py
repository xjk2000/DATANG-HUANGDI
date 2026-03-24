#!/usr/bin/env python3
"""
朝堂路由引擎 · 层级通信规则

定义三省六部五监的合法通信链路。
消息不允许越级发送，违规路由直接拒绝。
"""

# ─── 路由表：定义每个 Agent 可以发送消息给谁 ──────────────
# 规则：严格遵循三省六部组织结构
ROUTING_TABLE = {
    # 皇帝只下旨给中书令
    'emperor': {
        'can_send_to': ['zhongshuling'],
    },

    # ─── 中书省 ───
    'zhongshuling': {
        'can_send_to': ['zhongshu_sheren', 'shizhong'],
        # 中书令可以：请中书舍人分析、提交敕令给侍中
    },
    'zhongshu_sheren': {
        'can_send_to': ['zhongshuling'],
        # 中书舍人只回复中书令
    },

    # ─── 门下省 ───
    'shizhong': {
        'can_send_to': ['jishizhong', 'zhongshuling', 'shangshuling'],
        # 侍中可以：请给事中排查、封驳回中书令、准奏转尚书令
    },
    'jishizhong': {
        'can_send_to': ['shizhong'],
        # 给事中只回复侍中
    },

    # ─── 尚书省 ───
    'shangshuling': {
        'can_send_to': [
            'shizhong',
            # 六部
            'libu', 'hubu', 'libu_protocol', 'bingbu', 'xingbu', 'gongbu',
            # 五监
            'jiangzuo', 'shaofu', 'junqi', 'dushui', 'sinong',
        ],
        # 尚书令派发任务给六部五监，回报给侍中
    },

    # ─── 六部（只与尚书令通信）───
    'libu':            {'can_send_to': ['shangshuling']},
    'hubu':            {'can_send_to': ['shangshuling']},
    'libu_protocol':   {'can_send_to': ['shangshuling']},
    'bingbu':          {'can_send_to': ['shangshuling']},
    'xingbu':          {'can_send_to': ['shangshuling']},
    'gongbu':          {'can_send_to': ['shangshuling']},

    # ─── 五监（只与尚书令通信）───
    'jiangzuo':        {'can_send_to': ['shangshuling']},
    'shaofu':          {'can_send_to': ['shangshuling']},
    'junqi':           {'can_send_to': ['shangshuling']},
    'dushui':          {'can_send_to': ['shangshuling']},
    'sinong':          {'can_send_to': ['shangshuling']},
}


class RoutingError(Exception):
    """路由校验失败"""
    pass


def validate_route(from_agent, to_agent):
    """
    校验消息路由是否合法。

    :return: (True, '') 或 (False, '错误描述')
    """
    rule = ROUTING_TABLE.get(from_agent)
    if rule is None:
        return False, f"未知发送方: {from_agent}"

    if to_agent not in rule['can_send_to']:
        allowed = ', '.join(rule['can_send_to'])
        return False, f"禁止通信: {from_agent} → {to_agent} (允许目标: {allowed})"

    return True, ''


def get_allowed_targets(agent_id):
    """获取 Agent 可发送消息的目标列表"""
    rule = ROUTING_TABLE.get(agent_id)
    if rule is None:
        return []
    return list(rule['can_send_to'])


def get_all_agents():
    """获取所有已注册的 Agent ID 列表（不含 emperor）"""
    return [k for k in ROUTING_TABLE.keys() if k != 'emperor']


def get_upstream(agent_id):
    """获取 Agent 的上级（谁可以向它发消息）"""
    upstream = []
    for sender, rule in ROUTING_TABLE.items():
        if agent_id in rule['can_send_to']:
            upstream.append(sender)
    return upstream
