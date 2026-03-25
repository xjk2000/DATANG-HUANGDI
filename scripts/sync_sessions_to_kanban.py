#!/usr/bin/env python3
"""
从 OpenClaw Session 同步任务到看板。

读取 OpenClaw 的 session JSONL 文件，提取任务信息，
自动创建或更新看板任务。
"""

import json
import os
import glob
import sys
import re
from datetime import datetime, timezone
from pathlib import Path

# 确保能导入同目录的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from file_lock import locked_json_rw

REPO_DIR = os.environ.get('REPO_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(REPO_DIR, 'data')
# 支持通过环境变量配置 OpenClaw 路径，默认为 ~/.openclaw
OC_HOME = os.environ.get('OPENCLAW_HOME', os.path.join(str(Path.home()), '.openclaw'))
TASKS_FILE = os.path.join(DATA_DIR, 'tasks_source.json')
SYNC_STATE_FILE = os.path.join(DATA_DIR, 'session_sync_state.json')

# Agent 到部门的映射
AGENT_TO_ORG = {
    'zhongshuling': '中书省', 'zhongshu_sheren': '中书省',
    'shizhong': '门下省', 'jishizhong': '门下省',
    'shangshuling': '尚书省',
    'libu': '吏部', 'hubu': '户部', 'libu_protocol': '礼部',
    'bingbu': '兵部', 'xingbu': '刑部', 'gongbu': '工部',
    'jiangzuo': '将作监', 'shaofu': '少府监', 'junqi': '军器监',
    'dushui': '都水监', 'sinong': '司农监',
}

AGENT_NAMES = {
    'zhongshuling': '中书令', 'zhongshu_sheren': '中书舍人',
    'shizhong': '侍中侍郎', 'jishizhong': '给事中',
    'shangshuling': '尚书令',
    'libu': '吏部', 'hubu': '户部', 'libu_protocol': '礼部',
    'bingbu': '兵部', 'xingbu': '刑部', 'gongbu': '工部',
    'jiangzuo': '将作监', 'shaofu': '少府监', 'junqi': '军器监',
    'dushui': '都水监', 'sinong': '司农监',
}


def now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def get_session_files():
    """获取所有 Agent 的 session 文件"""
    sessions_dir = os.path.join(OC_HOME, 'sessions', 'transcripts')
    if not os.path.isdir(sessions_dir):
        return []
    
    session_files = []
    for agent_id in AGENT_TO_ORG.keys():
        agent_dir = os.path.join(sessions_dir, agent_id)
        if os.path.isdir(agent_dir):
            for f in glob.glob(os.path.join(agent_dir, '*.jsonl')):
                session_files.append({
                    'path': f,
                    'agent_id': agent_id,
                    'session_id': os.path.basename(f).replace('.jsonl', ''),
                    'mtime': os.path.getmtime(f),
                })
    
    return session_files


def load_sync_state():
    """加载同步状态（记录已处理的 session）"""
    if not os.path.exists(SYNC_STATE_FILE):
        return {}
    try:
        with open(SYNC_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_sync_state(state):
    """保存同步状态"""
    tmp_path = SYNC_STATE_FILE + f'.tmp-{os.getpid()}'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, SYNC_STATE_FILE)


def parse_session_file(filepath):
    """解析 session JSONL 文件，提取任务信息"""
    messages = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    messages.append(msg)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"[sync] 读取 session 文件失败 {filepath}: {e}")
        return None
    
    if not messages:
        return None
    
    # 提取任务信息
    # 假设第一条用户消息包含任务描述
    user_messages = [m for m in messages if m.get('role') == 'user']
    if not user_messages:
        return None
    
    first_user_msg = user_messages[0]
    content = first_user_msg.get('content', '')
    if isinstance(content, list):
        # 处理多模态内容
        text_parts = [c.get('text', '') for c in content if c.get('type') == 'text']
        content = '\n'.join(text_parts)
    
    # 提取标题（取第一行或前50个字符）
    title_match = content.split('\n')[0] if '\n' in content else content
    title = title_match[:50] + ('...' if len(title_match) > 50 else '')
    
    # 提取时间戳
    timestamp = first_user_msg.get('timestamp')
    if timestamp:
        try:
            created_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%Y-%m-%dT%H:%M:%SZ')
        except Exception:
            created_at = now_iso()
    else:
        created_at = now_iso()
    
    return {
        'title': title,
        'content': content,
        'created_at': created_at,
        'message_count': len(messages),
    }


def create_or_update_task(session_id, agent_id, task_info):
    """创建或更新看板任务"""
    task_id = f"SESSION-{agent_id}-{session_id[:8]}"
    
    def update_tasks(tasks):
        # 查找是否已存在
        existing = next((t for t in tasks if t['id'] == task_id), None)
        
        if existing:
            # 更新现有任务
            existing['updated_at'] = now_iso()
            existing['session_id'] = session_id
            existing['message_count'] = task_info['message_count']
            return tasks, 'updated'
        else:
            # 创建新任务
            new_task = {
                'id': task_id,
                'title': task_info['title'],
                'state': 'Executing',  # 默认状态为执行中
                'org': AGENT_TO_ORG.get(agent_id, '未知'),
                'official': agent_id,
                'official_name': AGENT_NAMES.get(agent_id, agent_id),
                'created_at': task_info['created_at'],
                'updated_at': now_iso(),
                'session_id': session_id,
                'message_count': task_info['message_count'],
                'source': 'openclaw_session',
                'content': task_info['content'][:200],  # 保存前200字符
            }
            tasks.append(new_task)
            return tasks, 'created'
    
    try:
        tasks, action = locked_json_rw(TASKS_FILE, update_tasks, default=[])
        return action
    except Exception as e:
        print(f"[sync] 创建/更新任务失败 {task_id}: {e}")
        return None


def sync_sessions():
    """同步所有新的 session 到看板"""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 加载同步状态
    sync_state = load_sync_state()
    
    # 获取所有 session 文件
    session_files = get_session_files()
    if not session_files:
        print("[sync] 未找到 OpenClaw session 文件")
        return
    
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    for session_file in session_files:
        session_id = session_file['session_id']
        agent_id = session_file['agent_id']
        filepath = session_file['path']
        mtime = session_file['mtime']
        
        # 检查是否已同步且未修改
        state_key = f"{agent_id}:{session_id}"
        if state_key in sync_state and sync_state[state_key].get('mtime') == mtime:
            skipped_count += 1
            continue
        
        # 解析 session 文件
        task_info = parse_session_file(filepath)
        if not task_info:
            skipped_count += 1
            continue
        
        # 创建或更新任务
        action = create_or_update_task(session_id, agent_id, task_info)
        if action == 'created':
            created_count += 1
            print(f"[sync] ✅ 创建任务: {agent_id}/{session_id[:8]} - {task_info['title']}")
        elif action == 'updated':
            updated_count += 1
            print(f"[sync] 🔄 更新任务: {agent_id}/{session_id[:8]}")
        
        # 更新同步状态
        sync_state[state_key] = {
            'mtime': mtime,
            'synced_at': now_iso(),
        }
    
    # 保存同步状态
    save_sync_state(sync_state)
    
    print(f"[sync] 完成: {created_count} 新建, {updated_count} 更新, {skipped_count} 跳过")


def main():
    sync_sessions()


if __name__ == '__main__':
    main()
