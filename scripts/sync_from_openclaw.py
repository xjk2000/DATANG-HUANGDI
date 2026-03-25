#!/usr/bin/env python3
"""
从 OpenClaw 运行时同步数据到帝王系统。

读取 OpenClaw 的 session JSONL 文件，提取活跃会话信息，
更新 live_status.json 供看板展示。
"""

import json
import os
import glob
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_DIR = os.environ.get('REPO_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(REPO_DIR, 'data')
# 支持通过环境变量配置 OpenClaw 路径，默认为 ~/.openclaw
OC_HOME = os.environ.get('OPENCLAW_HOME', os.path.join(str(Path.home()), '.openclaw'))

# 所有 Agent ID
ALL_AGENTS = [
    'zhongshuling', 'zhongshu_sheren',
    'shizhong', 'jishizhong',
    'shangshuling',
    'libu', 'hubu', 'libu_protocol', 'bingbu', 'xingbu', 'gongbu',
    'jiangzuo', 'shaofu', 'junqi', 'dushui', 'sinong',
]

AGENT_NAMES = {
    'zhongshuling': '中书令', 'zhongshu_sheren': '中书舍人',
    'shizhong': '侍中侍郎', 'jishizhong': '给事中',
    'shangshuling': '尚书令',
    'libu': '吏部', 'hubu': '户部', 'libu_protocol': '礼部',
    'bingbu': '兵部', 'xingbu': '刑部', 'gongbu': '工部',
    'jiangzuo': '将作监', 'shaofu': '少府监', 'junqi': '军器监',
    'dushui': '都水监', 'sinong': '司农监',
}

AGENT_GROUPS = {
    'zhongshuling': '中书省', 'zhongshu_sheren': '中书省',
    'shizhong': '门下省', 'jishizhong': '门下省',
    'shangshuling': '尚书省',
    'libu': '六部', 'hubu': '六部', 'libu_protocol': '六部',
    'bingbu': '六部', 'xingbu': '六部', 'gongbu': '六部',
    'jiangzuo': '五监', 'shaofu': '五监', 'junqi': '五监',
    'dushui': '五监', 'sinong': '五监',
}


def now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def get_agent_sessions_dir(agent_id):
    """获取 Agent 的 session transcripts 目录"""
    return os.path.join(OC_HOME, 'sessions', 'transcripts', agent_id)


def count_sessions(agent_id):
    """统计 Agent 的会话数"""
    sessions_dir = get_agent_sessions_dir(agent_id)
    if not os.path.isdir(sessions_dir):
        return 0
    return len(glob.glob(os.path.join(sessions_dir, '*.jsonl')))


def get_last_activity(agent_id):
    """获取 Agent 最后活跃时间"""
    sessions_dir = get_agent_sessions_dir(agent_id)
    if not os.path.isdir(sessions_dir):
        return None

    latest_mtime = 0
    for f in glob.glob(os.path.join(sessions_dir, '*.jsonl')):
        mtime = os.path.getmtime(f)
        if mtime > latest_mtime:
            latest_mtime = mtime

    if latest_mtime == 0:
        return None
    return datetime.fromtimestamp(latest_mtime, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def check_agent_alive(agent_id):
    """检查 Agent 是否活跃（最近 5 分钟有活动）"""
    last = get_last_activity(agent_id)
    if not last:
        return 'unknown'
    try:
        last_dt = datetime.fromisoformat(last.replace('Z', '+00:00'))
        now_dt = datetime.now(timezone.utc)
        delta = (now_dt - last_dt).total_seconds()
        if delta < 300:
            return 'alive'
        elif delta < 1800:
            return 'idle'
        else:
            return 'inactive'
    except Exception:
        return 'unknown'


def sync_live_status():
    """同步所有 Agent 的实时状态"""
    status = {}
    for agent_id in ALL_AGENTS:
        status[agent_id] = {
            'id': agent_id,
            'name': AGENT_NAMES.get(agent_id, agent_id),
            'group': AGENT_GROUPS.get(agent_id, '未知'),
            'status': check_agent_alive(agent_id),
            'sessions': count_sessions(agent_id),
            'lastActivity': get_last_activity(agent_id),
            'updatedAt': now_iso(),
        }

    output_path = os.path.join(DATA_DIR, 'live_status.json')
    tmp_path = output_path + f'.tmp-{os.getpid()}'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, output_path)

    alive = sum(1 for v in status.values() if v['status'] == 'alive')
    total = len(status)
    print(f"[sync] live_status 已更新: {alive}/{total} agents 活跃")


def sync_agent_config():
    """同步 Agent 配置信息"""
    oc_cfg_path = os.path.join(OC_HOME, 'openclaw.json')
    if not os.path.exists(oc_cfg_path):
        print("[sync] openclaw.json 不存在，跳过配置同步")
        return

    try:
        with open(oc_cfg_path, 'r', encoding='utf-8') as f:
            oc_cfg = json.load(f)
    except Exception as e:
        print(f"[sync] 读取 openclaw.json 失败: {e}")
        return

    agents_list = oc_cfg.get('agents', {}).get('list', [])
    config = {}
    for agent in agents_list:
        agent_id = agent.get('id', '')
        if agent_id in ALL_AGENTS:
            model = agent.get('model', {})
            if isinstance(model, str):
                model_name = model
            elif isinstance(model, dict):
                model_name = model.get('primary', '默认')
            else:
                model_name = '默认'

            config[agent_id] = {
                'id': agent_id,
                'name': AGENT_NAMES.get(agent_id, agent_id),
                'workspace': agent.get('workspace', ''),
                'model': model_name,
                'subagents': agent.get('subagents', {}),
            }

    output_path = os.path.join(DATA_DIR, 'agent_config.json')
    tmp_path = output_path + f'.tmp-{os.getpid()}'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, output_path)

    print(f"[sync] agent_config 已更新: {len(config)} agents")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    sync_live_status()
    sync_agent_config()


if __name__ == '__main__':
    main()
