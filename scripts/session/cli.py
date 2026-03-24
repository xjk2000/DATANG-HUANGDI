#!/usr/bin/env python3
"""
朝堂会话 CLI · Agent 收发消息命令行工具

用法：
    python3 scripts/session/cli.py send <from> <to> <task_id> <msg_type> "<内容>"
    python3 scripts/session/cli.py reply <from> <ref_msg_id> "<内容>"
    python3 scripts/session/cli.py reject <from> <ref_msg_id> "<理由>"
    python3 scripts/session/cli.py inbox <agent_id> [--status pending]
    python3 scripts/session/cli.py read <agent_id> <msg_id>
    python3 scripts/session/cli.py ack <agent_id> <msg_id>
    python3 scripts/session/cli.py thread <task_id>
    python3 scripts/session/cli.py conversations
    python3 scripts/session/cli.py routes <agent_id>
"""

import json
import os
import sys

# 确保能导入同目录和父目录模块
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, SCRIPTS_DIR)

from session.message import format_message, format_message_brief, MSG_TYPES, agent_display_name
from session.message_bus import bus
from session.router import RoutingError, get_allowed_targets, get_upstream, get_all_agents
from session.session_store import get_inbox, get_message, get_thread, list_conversations, count_inbox


# ─── 输出辅助 ─────────────────────────────────────────────

def print_ok(msg):
    print(f"\033[0;32m✅ {msg}\033[0m")

def print_err(msg):
    print(f"\033[0;31m❌ {msg}\033[0m", file=sys.stderr)

def print_info(msg):
    print(f"\033[0;34mℹ️  {msg}\033[0m")

def print_msg(msg):
    """打印完整的格式化消息"""
    print(format_message(msg))


# ─── 命令实现 ─────────────────────────────────────────────

def cmd_send(args):
    """发送消息"""
    if len(args) < 5:
        print_err("用法: send <from> <to> <task_id> <msg_type> <内容>")
        print_err(f"消息类型: {', '.join(MSG_TYPES)}")
        sys.exit(1)

    from_agent, to_agent, task_id, msg_type, content = args[0], args[1], args[2], args[3], args[4]

    # 附加元数据
    metadata = {}
    i = 5
    while i < len(args):
        if args[i] == '--ref' and i + 1 < len(args):
            metadata['ref_msg_id'] = args[i + 1]
            i += 2
        else:
            i += 1

    ref_msg_id = metadata.pop('ref_msg_id', '')

    try:
        msg = bus.send(from_agent, to_agent, task_id, msg_type, content,
                       ref_msg_id=ref_msg_id, metadata=metadata)
        print_ok(f"消息已发送: {msg['msg_id']}")
        print_msg(msg)
    except RoutingError as e:
        print_err(f"路由拒绝: {e}")
        sys.exit(1)
    except ValueError as e:
        print_err(str(e))
        sys.exit(1)


def cmd_reply(args):
    """回复消息"""
    if len(args) < 3:
        print_err("用法: reply <from> <ref_msg_id> <内容>")
        sys.exit(1)

    from_agent, ref_msg_id, content = args[0], args[1], args[2]

    try:
        msg = bus.reply(from_agent, ref_msg_id, content)
        print_ok(f"回复已发送: {msg['msg_id']}")
        print_msg(msg)
    except RoutingError as e:
        print_err(f"路由拒绝: {e}")
        sys.exit(1)
    except ValueError as e:
        print_err(str(e))
        sys.exit(1)


def cmd_reject(args):
    """封驳消息"""
    if len(args) < 3:
        print_err("用法: reject <from> <ref_msg_id> <理由>")
        sys.exit(1)

    from_agent, ref_msg_id, reason = args[0], args[1], args[2]

    try:
        msg = bus.reject(from_agent, ref_msg_id, reason)
        print_ok(f"封驳已发送: {msg['msg_id']}")
        print_msg(msg)
    except RoutingError as e:
        print_err(f"路由拒绝: {e}")
        sys.exit(1)
    except ValueError as e:
        print_err(str(e))
        sys.exit(1)


def cmd_inbox(args):
    """查看收件箱"""
    if len(args) < 1:
        print_err("用法: inbox <agent_id> [--status pending]")
        sys.exit(1)

    agent_id = args[0]
    status_filter = None
    i = 1
    while i < len(args):
        if args[i] == '--status' and i + 1 < len(args):
            status_filter = args[i + 1]
            i += 2
        else:
            i += 1

    messages = get_inbox(agent_id, status_filter)
    name = agent_display_name(agent_id)
    pending = count_inbox(agent_id, 'pending')

    print_info(f"{name} 收件箱 (共 {len(messages)} 条, 待处理 {pending} 条)")
    if not messages:
        print("  （空）")
        return

    for msg in messages:
        print(f"  {format_message_brief(msg)}")


def cmd_read(args):
    """读取单条消息"""
    if len(args) < 2:
        print_err("用法: read <agent_id> <msg_id>")
        sys.exit(1)

    agent_id, msg_id = args[0], args[1]
    msg = get_message(agent_id, msg_id)
    if msg is None:
        print_err(f"未找到消息: {msg_id}（在 {agent_id} 收件箱中）")
        sys.exit(1)

    # 标记为已读
    bus.mark_read(agent_id, msg_id)

    print(format_message(msg))
    print()
    print(f"  类型: {msg['msg_type']}")
    print(f"  状态: {msg.get('status', '?')}")
    print(f"  时间: {msg['created_at']}")
    if msg.get('ref_msg_id'):
        print(f"  引用: {msg['ref_msg_id']}")
    if msg.get('metadata'):
        print(f"  元数据: {json.dumps(msg['metadata'], ensure_ascii=False)}")


def cmd_ack(args):
    """确认消息已处理"""
    if len(args) < 2:
        print_err("用法: ack <agent_id> <msg_id>")
        sys.exit(1)

    agent_id, msg_id = args[0], args[1]
    ok = bus.ack(agent_id, msg_id)
    if ok:
        print_ok(f"消息已确认: {msg_id}")
    else:
        print_err(f"消息不存在: {msg_id}")
        sys.exit(1)


def cmd_thread(args):
    """查看任务会话线程"""
    if len(args) < 1:
        print_err("用法: thread <task_id>")
        sys.exit(1)

    task_id = args[0]
    thread = get_thread(task_id)

    if not thread:
        print_info(f"任务 {task_id} 暂无会话记录")
        return

    print_info(f"任务 {task_id} 会话线程 ({len(thread)} 条消息)")
    print()
    for msg in thread:
        print(f"  {format_message_brief(msg)}")
    print()


def cmd_conversations(args):
    """列出所有有会话记录的任务"""
    tasks = list_conversations()
    if not tasks:
        print_info("暂无会话记录")
        return

    print_info(f"共 {len(tasks)} 个任务有会话记录")
    for task_id in tasks:
        thread = get_thread(task_id)
        print(f"  📋 {task_id} ({len(thread)} 条消息)")


def cmd_routes(args):
    """查看 Agent 的路由信息"""
    if len(args) < 1:
        # 显示全部路由表
        print_info("朝堂路由表（合法通信链路）")
        print()
        for agent_id in get_all_agents():
            name = agent_display_name(agent_id)
            targets = get_allowed_targets(agent_id)
            target_names = [agent_display_name(t) for t in targets]
            print(f"  {name} → {', '.join(target_names)}")
        return

    agent_id = args[0]
    name = agent_display_name(agent_id)
    targets = get_allowed_targets(agent_id)
    upstream = get_upstream(agent_id)

    if not targets and not upstream:
        print_err(f"未知 Agent: {agent_id}")
        sys.exit(1)

    print_info(f"{name} ({agent_id}) 的通信链路")
    print()
    print(f"  可发送给: {', '.join(agent_display_name(t) for t in targets) or '无'}")
    print(f"  接收来自: {', '.join(agent_display_name(u) for u in upstream) or '无'}")


# ─── 主入口 ───────────────────────────────────────────────

COMMANDS = {
    'send':          cmd_send,
    'reply':         cmd_reply,
    'reject':        cmd_reject,
    'inbox':         cmd_inbox,
    'read':          cmd_read,
    'ack':           cmd_ack,
    'thread':        cmd_thread,
    'conversations': cmd_conversations,
    'routes':        cmd_routes,
}


def main():
    if len(sys.argv) < 2:
        print_err(f"用法: {sys.argv[0]} <command> [args...]")
        print_err(f"可用命令: {', '.join(COMMANDS.keys())}")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)

    if cmd not in COMMANDS:
        print_err(f"未知命令: {cmd}")
        print_err(f"可用命令: {', '.join(COMMANDS.keys())}")
        sys.exit(1)

    COMMANDS[cmd](sys.argv[2:])


if __name__ == '__main__':
    main()
