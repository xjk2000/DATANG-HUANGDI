#!/usr/bin/env python3
"""
飞书渠道配置管理

存储结构：
  data/feishu_channels.json
  {
    "zhongshuling": {
      "app_id": "cli_a5xxxx",
      "app_secret": "xxxxx",
      "enabled": true,
      "bot_name": "中书令",
      "webhook_token": "auto-generated-verify-token",
      "created_at": "...",
      "updated_at": "..."
    },
    ...
  }
"""

import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from file_lock import FileLock

REPO_DIR = os.environ.get('REPO_DIR', os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = os.path.join(REPO_DIR, 'data')
CHANNELS_FILE = os.path.join(DATA_DIR, 'feishu_channels.json')


def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _load_channels():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CHANNELS_FILE):
        return {}
    try:
        with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_channels(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    lock_path = os.path.join(DATA_DIR, '.lock_feishu_channels')
    with FileLock(lock_path, timeout=5):
        tmp = CHANNELS_FILE + f'.tmp-{os.getpid()}'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, CHANNELS_FILE)


def get_all_channels():
    """获取所有渠道配置"""
    return _load_channels()


def get_channel(agent_id):
    """获取单个 Agent 的飞书渠道配置"""
    channels = _load_channels()
    return channels.get(agent_id)


def save_channel(agent_id, app_id, app_secret, bot_name='', enabled=True):
    """保存或更新 Agent 的飞书渠道配置"""
    channels = _load_channels()
    existing = channels.get(agent_id, {})

    channels[agent_id] = {
        'app_id': app_id,
        'app_secret': app_secret,
        'bot_name': bot_name or agent_id,
        'enabled': enabled,
        'webhook_token': existing.get('webhook_token') or uuid.uuid4().hex[:16],
        'created_at': existing.get('created_at', _now_iso()),
        'updated_at': _now_iso(),
    }
    _save_channels(channels)
    return channels[agent_id]


def delete_channel(agent_id):
    """删除 Agent 的飞书渠道配置"""
    channels = _load_channels()
    if agent_id in channels:
        del channels[agent_id]
        _save_channels(channels)
        return True
    return False


def toggle_channel(agent_id, enabled):
    """启用/禁用渠道"""
    channels = _load_channels()
    if agent_id not in channels:
        return False
    channels[agent_id]['enabled'] = enabled
    channels[agent_id]['updated_at'] = _now_iso()
    _save_channels(channels)
    return True


def test_channel(agent_id):
    """
    测试飞书渠道连接。
    调用飞书 API 获取 tenant_access_token 验证凭证有效性。
    """
    channel = get_channel(agent_id)
    if not channel:
        return {'ok': False, 'error': f'未找到 {agent_id} 的飞书配置'}

    app_id = channel.get('app_id', '')
    app_secret = channel.get('app_secret', '')
    if not app_id or not app_secret:
        return {'ok': False, 'error': '缺少 app_id 或 app_secret'}

    try:
        import urllib.request
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
                return {
                    'ok': True,
                    'tenant_access_token': result.get('tenant_access_token', '')[:8] + '...',
                    'expire': result.get('expire', 0),
                }
            else:
                return {'ok': False, 'error': result.get('msg', '未知错误')}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
