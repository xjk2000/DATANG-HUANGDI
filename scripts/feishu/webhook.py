#!/usr/bin/env python3
"""
飞书 Webhook 接收器

接收飞书机器人的事件回调，将消息转发给对应的 Agent。
支持：
  - URL 验证（challenge）
  - 消息接收（im.message.receive_v1）
  - 转发到朝堂消息总线

启动：
    python3 scripts/feishu/webhook.py [--port 7892]
"""

import hashlib
import hmac
import http.server
import json
import os
import socketserver
import sys
import time
import urllib.parse
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, SCRIPTS_DIR)

from feishu.config import get_all_channels, get_channel

REPO_DIR = os.environ.get('REPO_DIR', os.path.dirname(os.path.dirname(SCRIPTS_DIR)))
DATA_DIR = os.path.join(REPO_DIR, 'data')
WEBHOOK_PORT = int(os.environ.get('FEISHU_WEBHOOK_PORT', 7892))

# Agent ID ↔ App ID 反向映射（启动时构建）
_app_to_agent = {}


def _rebuild_app_map():
    global _app_to_agent
    channels = get_all_channels()
    _app_to_agent = {}
    for agent_id, cfg in channels.items():
        app_id = cfg.get('app_id', '')
        if app_id and cfg.get('enabled', False):
            _app_to_agent[app_id] = agent_id


def _get_tenant_token(app_id, app_secret):
    """获取飞书 tenant_access_token"""
    req_data = json.dumps({
        'app_id': app_id,
        'app_secret': app_secret,
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
        data=req_data,
        headers={'Content-Type': 'application/json; charset=utf-8'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        if result.get('code') == 0:
            return result.get('tenant_access_token', '')
    return ''


def _send_feishu_reply(token, message_id, text):
    """通过飞书 API 回复消息"""
    req_data = json.dumps({
        'content': json.dumps({'text': text}),
        'msg_type': 'text',
    }).encode('utf-8')
    req = urllib.request.Request(
        f'https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply',
        data=req_data,
        headers={
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': f'Bearer {token}',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {'code': -1, 'msg': str(e)}


def _log(msg):
    ts = time.strftime('%H:%M:%S')
    print(f"[{ts}] {msg}")


class FeishuWebhookHandler(http.server.BaseHTTPRequestHandler):
    """飞书 Webhook 请求处理器"""

    def log_message(self, format, *args):
        ts = time.strftime('%H:%M:%S')
        print(f"[{ts}] {args[0]}" if args else f"[{ts}] {format}")

    def _json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._json_response({'error': 'invalid json'}, 400)
            return

        # URL 验证（飞书首次配置回调地址时发送）
        if 'challenge' in data:
            _log(f"URL 验证: challenge={data['challenge'][:16]}...")
            self._json_response({'challenge': data['challenge']})
            return

        # 事件 v2 格式
        header = data.get('header', {})
        event = data.get('event', {})
        event_type = header.get('event_type', '')
        app_id = header.get('app_id', '')

        if event_type == 'im.message.receive_v1':
            self._handle_message(app_id, event)
            self._json_response({'code': 0})
        else:
            _log(f"未处理事件: {event_type}")
            self._json_response({'code': 0})

    def _handle_message(self, app_id, event):
        """处理收到的飞书消息"""
        _rebuild_app_map()

        agent_id = _app_to_agent.get(app_id)
        if not agent_id:
            _log(f"未知 app_id: {app_id}，忽略消息")
            return

        sender = event.get('sender', {}).get('sender_id', {})
        message = event.get('message', {})
        msg_type = message.get('message_type', '')
        message_id = message.get('message_id', '')
        chat_id = message.get('chat_id', '')

        # 只处理文本消息
        if msg_type != 'text':
            _log(f"[{agent_id}] 忽略非文本消息: {msg_type}")
            return

        try:
            content_json = json.loads(message.get('content', '{}'))
            text = content_json.get('text', '').strip()
        except json.JSONDecodeError:
            text = ''

        if not text:
            return

        _log(f"[{agent_id}] 收到飞书消息: {text[:60]}")

        # 将消息写入 Agent 收件箱（作为皇帝旨意或外部输入）
        try:
            from session.message_bus import bus
            from session.message import agent_display_name

            # 如果消息以 @agent_id 开头，路由到对应 Agent
            # 否则默认作为对当前 Agent 的指令
            msg = bus.send(
                from_agent='emperor',
                to_agent='zhongshuling' if agent_id == 'zhongshuling' else agent_id,
                task_id=f"FEISHU-{int(time.time())}",
                msg_type='edict',
                content=text,
                metadata={'source': 'feishu', 'message_id': message_id, 'chat_id': chat_id},
            )
            _log(f"[{agent_id}] 已转发到朝堂: {msg['msg_id']}")

            # 回复确认
            channel = get_channel(agent_id)
            if channel:
                token = _get_tenant_token(channel['app_id'], channel['app_secret'])
                if token:
                    name = agent_display_name(agent_id)
                    _send_feishu_reply(token, message_id,
                                       f"📜 {name}已接旨 (任务ID: {msg['task_id']})")

        except Exception as e:
            _log(f"[{agent_id}] 转发失败: {e}")

    def do_GET(self):
        if self.path == '/health':
            _rebuild_app_map()
            self._json_response({
                'status': 'ok',
                'agents': list(_app_to_agent.values()),
                'port': WEBHOOK_PORT,
            })
        else:
            self._json_response({'error': 'not found'}, 404)


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    _rebuild_app_map()

    print()
    print('\033[0;36m╔════════════════════════════════════════╗\033[0m')
    print('\033[0;36m║  📡 飞书 Webhook 接收器                ║\033[0m')
    print('\033[0;36m╚════════════════════════════════════════╝\033[0m')
    print()
    print(f'  🔗 Webhook URL: http://0.0.0.0:{WEBHOOK_PORT}/')
    print(f'  💚 健康检查:    http://127.0.0.1:{WEBHOOK_PORT}/health')
    print(f'  📋 已绑定 Agent: {list(_app_to_agent.values()) or "(无)"}')
    print()
    print('  配置飞书机器人事件订阅 URL 为:')
    print(f'    http://<你的公网IP>:{WEBHOOK_PORT}/')
    print()

    with ReusableTCPServer(('', WEBHOOK_PORT), FeishuWebhookHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n\033[0;33m⚠️  Webhook 服务已停止\033[0m')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='飞书 Webhook 接收器')
    parser.add_argument('--port', type=int, default=WEBHOOK_PORT, help='监听端口')
    args = parser.parse_args()
    WEBHOOK_PORT = args.port
    main()
