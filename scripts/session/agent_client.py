#!/usr/bin/env python3
"""
Agent 朝堂监听客户端

每个 Agent 运行一个实例，连接到朝堂 WebSocket 服务器。
- 监听所有消息
- 当 to_agent == 自己时，自动"接旨"并调用 OpenClaw
- 支持断线重连
"""

import asyncio
import json
import os
import subprocess
import sys
import time
import websockets

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, SCRIPTS_DIR)

from session.message import agent_display_name

REPO_DIR = os.environ.get('REPO_DIR', os.path.dirname(os.path.dirname(SCRIPTS_DIR)))
WS_URL = os.environ.get('COURT_WS_URL', 'ws://127.0.0.1:7893')
OC_HOME = os.path.expanduser(os.environ.get('OC_HOME', '~/.openclaw'))


def _log(agent_id, msg):
    ts = time.strftime('%H:%M:%S')
    name = agent_display_name(agent_id)
    print(f"[{ts}] [{name}] {msg}")


def _call_openclaw(agent_id, message_content, task_id):
    """
    调用 OpenClaw 向 Agent 发送消息。
    
    使用 openclaw chat send 命令。
    """
    try:
        cmd = [
            'openclaw', 'chat', 'send',
            '--agent', agent_id,
            '--message', f"【朝堂旨意】任务ID: {task_id}\n\n{message_content}",
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    
    except subprocess.TimeoutExpired:
        return False, "OpenClaw 调用超时"
    except FileNotFoundError:
        return False, "未找到 openclaw 命令，请确保已安装 OpenClaw"
    except Exception as e:
        return False, str(e)


async def listen_court(agent_id):
    """连接朝堂并监听消息"""
    name = agent_display_name(agent_id)
    retry_delay = 5
    
    while True:
        try:
            _log(agent_id, f"正在连接朝堂 {WS_URL}...")
            
            async with websockets.connect(WS_URL) as ws:
                # 注册
                await ws.send(json.dumps({
                    'type': 'register',
                    'agent_id': agent_id,
                    'type': 'agent',
                }))
                
                _log(agent_id, "✅ 已进入朝堂，开始监听...")
                retry_delay = 5  # 重置重连延迟
                
                # 监听消息
                async for message in ws:
                    try:
                        data = json.loads(message)
                        msg_type = data.get('type')
                        
                        if msg_type == 'message':
                            await handle_message(agent_id, ws, data)
                        elif msg_type == 'system':
                            _log(agent_id, f"📢 {data.get('content', '')}")
                        elif msg_type == 'online':
                            clients = data.get('clients', [])
                            _log(agent_id, f"👥 在线: {len(clients)} 人")
                    
                    except json.JSONDecodeError:
                        _log(agent_id, f"⚠️  无效消息: {message[:100]}")
                    except Exception as e:
                        _log(agent_id, f"⚠️  处理消息失败: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            _log(agent_id, f"❌ 连接断开，{retry_delay}秒后重连...")
        except Exception as e:
            _log(agent_id, f"❌ 连接失败: {e}，{retry_delay}秒后重连...")
        
        await asyncio.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, 60)  # 指数退避，最多60秒


async def handle_message(agent_id, ws, data):
    """处理收到的消息"""
    from_agent = data.get('from_agent', '')
    to_agent = data.get('to_agent', '')
    content = data.get('content', '')
    task_id = data.get('task_id', '')
    msg_id = data.get('msg_id', '')
    from_name = data.get('from_name', '')
    
    # 判断是否是发给自己的
    is_for_me = (to_agent == agent_id or to_agent == 'all')
    
    if is_for_me and from_agent != agent_id:
        _log(agent_id, f"📩 收到旨意: {from_name} → {content[:60]}")
        
        # 自动回复"已接旨"
        await ws.send(json.dumps({
            'type': 'message',
            'to_agent': from_agent,
            'task_id': task_id,
            'msg_type': 'reply',
            'content': f"臣{agent_display_name(agent_id)}已接旨！正在处理...",
        }))
        
        # 调用 OpenClaw 执行任务
        _log(agent_id, f"🔧 调用 OpenClaw 处理任务...")
        ok, output = _call_openclaw(agent_id, content, task_id)
        
        if ok:
            _log(agent_id, f"✅ OpenClaw 调用成功")
            # 可选：将执行结果回复到朝堂
            # await ws.send(json.dumps({
            #     'type': 'message',
            #     'to_agent': from_agent,
            #     'task_id': task_id,
            #     'msg_type': 'report',
            #     'content': f"任务 {task_id} 已完成",
            # }))
        else:
            _log(agent_id, f"❌ OpenClaw 调用失败: {output}")
    else:
        # 不是发给自己的，只记录
        if to_agent != agent_id:
            _log(agent_id, f"💬 {from_name} → {data.get('to_name', '')}: {content[:40]}")


async def main():
    if len(sys.argv) < 2:
        print("用法: python3 agent_client.py <agent_id>")
        print("示例: python3 agent_client.py zhongshuling")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    name = agent_display_name(agent_id)
    
    print()
    print(f'\033[0;36m╔════════════════════════════════════════╗\033[0m')
    print(f'\033[0;36m║  👤 {name} 朝堂监听客户端{" " * (24 - len(name))}║\033[0m')
    print(f'\033[0;36m╚════════════════════════════════════════╝\033[0m')
    print()
    
    await listen_court(agent_id)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n\033[0;33m⚠️  监听已停止\033[0m')
