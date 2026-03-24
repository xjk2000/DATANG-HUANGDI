#!/usr/bin/env python3
"""
朝堂会话室 WebSocket 服务器

实时群聊模式，所有 Agent 和皇帝都在同一个"朝堂"中。
- 消息广播给所有连接的客户端
- Agent 监听到 to:自己 时自动接旨并执行
- 支持路由校验（可选）
- 持久化到 data/conversations/
"""

import asyncio
import json
import os
import sys
import time
import websockets
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, SCRIPTS_DIR)

from session.message import (
    create_message, format_message, agent_display_name,
    MSG_TYPE_LABELS, now_iso, gen_msg_id,
)
from session.router import validate_route
from session.session_store import append_to_thread, session_audit_log

REPO_DIR = os.environ.get('REPO_DIR', os.path.dirname(os.path.dirname(SCRIPTS_DIR)))
PORT = int(os.environ.get('COURT_WS_PORT', 7893))

# 所有连接的客户端 {websocket: {'agent_id': 'zhongshuling', 'type': 'agent'|'web'}}
clients = {}


def _log(msg):
    ts = time.strftime('%H:%M:%S')
    print(f"[{ts}] {msg}")


async def register_client(websocket, data):
    """注册客户端（Agent 或 Web）"""
    agent_id = data.get('agent_id', 'emperor')
    client_type = data.get('type', 'web')  # 'agent' or 'web'
    
    clients[websocket] = {
        'agent_id': agent_id,
        'type': client_type,
        'name': agent_display_name(agent_id),
        'connected_at': now_iso(),
    }
    
    _log(f"✅ {client_type.upper()} 连接: {agent_display_name(agent_id)} ({agent_id})")
    
    # 广播上线通知
    await broadcast({
        'type': 'system',
        'content': f"📥 {agent_display_name(agent_id)} 进入朝堂",
        'timestamp': now_iso(),
    }, exclude=websocket)
    
    # 发送当前在线列表
    online = [
        {'agent_id': c['agent_id'], 'name': c['name'], 'type': c['type']}
        for c in clients.values()
    ]
    await websocket.send(json.dumps({
        'type': 'online',
        'clients': online,
    }))


async def unregister_client(websocket):
    """注销客户端"""
    if websocket in clients:
        client = clients[websocket]
        _log(f"❌ {client['type'].upper()} 断开: {client['name']} ({client['agent_id']})")
        
        # 广播下线通知
        await broadcast({
            'type': 'system',
            'content': f"📤 {client['name']} 退出朝堂",
            'timestamp': now_iso(),
        }, exclude=websocket)
        
        del clients[websocket]


async def broadcast(message, exclude=None):
    """广播消息给所有客户端（可排除某个）"""
    if not clients:
        return
    
    msg_json = json.dumps(message, ensure_ascii=False)
    tasks = []
    for ws in clients:
        if ws != exclude:
            tasks.append(ws.send(msg_json))
    
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def handle_message(websocket, data):
    """处理收到的消息"""
    sender = clients.get(websocket, {})
    from_agent = sender.get('agent_id', 'emperor')
    to_agent = data.get('to_agent', '')
    task_id = data.get('task_id', f"COURT-{int(time.time())}")
    msg_type = data.get('msg_type', 'request')
    content = data.get('content', '')
    
    if not content:
        return
    
    # 路由校验（可选，Web 端发送时跳过）
    if sender.get('type') == 'agent' and to_agent:
        ok, err = validate_route(from_agent, to_agent)
        if not ok:
            await websocket.send(json.dumps({
                'type': 'error',
                'content': f"路由拒绝: {err}",
                'timestamp': now_iso(),
            }))
            return
    
    # 创建消息
    msg = create_message(
        from_agent=from_agent,
        to_agent=to_agent or 'all',
        task_id=task_id,
        msg_type=msg_type,
        content=content,
        metadata={'source': 'court'},
    )
    
    # 持久化
    append_to_thread(task_id, msg)
    session_audit_log(
        f"COURT {msg['msg_id']} | {agent_display_name(from_agent)}→"
        f"{agent_display_name(to_agent) if to_agent else '全体'} | {content[:60]}"
    )
    
    # 广播给所有人
    await broadcast({
        'type': 'message',
        'msg_id': msg['msg_id'],
        'from_agent': from_agent,
        'from_name': agent_display_name(from_agent),
        'to_agent': to_agent or 'all',
        'to_name': agent_display_name(to_agent) if to_agent else '全体',
        'task_id': task_id,
        'msg_type': msg_type,
        'msg_type_label': MSG_TYPE_LABELS.get(msg_type, msg_type),
        'content': content,
        'formatted': format_message(msg),
        'timestamp': msg['created_at'],
    })
    
    _log(f"📨 {agent_display_name(from_agent)} → {agent_display_name(to_agent) if to_agent else '全体'}: {content[:40]}")


async def handler(websocket):
    """WebSocket 连接处理器"""
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type')
                
                if msg_type == 'register':
                    await register_client(websocket, data)
                elif msg_type == 'message':
                    await handle_message(websocket, data)
                elif msg_type == 'ping':
                    await websocket.send(json.dumps({'type': 'pong'}))
                
            except json.JSONDecodeError:
                _log(f"⚠️  无效 JSON: {message[:100]}")
            except Exception as e:
                _log(f"⚠️  处理消息失败: {e}")
    
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await unregister_client(websocket)


async def main():
    print()
    print('\033[0;33m╔════════════════════════════════════════╗\033[0m')
    print('\033[0;33m║  🏛️  朝堂会话室 WebSocket 服务器       ║\033[0m')
    print('\033[0;33m╚════════════════════════════════════════╝\033[0m')
    print()
    print(f'  🔗 WebSocket: ws://0.0.0.0:{PORT}')
    print(f'  📋 Web 界面:  http://127.0.0.1:7891/court.html')
    print(f'  👥 在线客户端: 0')
    print()
    
    async with websockets.serve(handler, '0.0.0.0', PORT):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n\033[0;33m⚠️  朝堂会话室已关闭\033[0m')
