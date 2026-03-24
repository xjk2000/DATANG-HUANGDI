#!/usr/bin/env python3
"""
朝堂会话存储 · Session Store

存储结构（文件系统）：
  data/
  ├── inbox/                    # 收件箱（按 agent 分目录）
  │   ├── zhongshuling/
  │   │   ├── MSG-a1b2c3d4.json
  │   │   └── MSG-e5f6g7h8.json
  │   └── shizhong/
  ├── conversations/            # 会话线程（按任务分）
  │   └── T-042/
  │       └── thread.json       # [msg1, msg2, msg3, ...]
  └── session_audit.log         # 会话审计日志
"""

import json
import os
import sys
import glob

# 确保能导入同目录和父目录模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from file_lock import FileLock

# ─── 路径 ─────────────────────────────────────────────────
REPO_DIR = os.environ.get('REPO_DIR', os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = os.path.join(REPO_DIR, 'data')
INBOX_DIR = os.path.join(DATA_DIR, 'inbox')
CONV_DIR = os.path.join(DATA_DIR, 'conversations')
SESSION_LOG = os.path.join(DATA_DIR, 'session_audit.log')


def _ensure_dirs():
    os.makedirs(INBOX_DIR, exist_ok=True)
    os.makedirs(CONV_DIR, exist_ok=True)


def session_audit_log(msg):
    """追加会话审计日志"""
    from session.message import now_iso
    ts = now_iso()
    line = f"[{ts}] {msg}\n"
    _ensure_dirs()
    try:
        with open(SESSION_LOG, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        pass


# ─── Inbox 操作 ────────────────────────────────────────────

def _inbox_dir(agent_id):
    d = os.path.join(INBOX_DIR, agent_id)
    os.makedirs(d, exist_ok=True)
    return d


def _inbox_path(agent_id, msg_id):
    return os.path.join(_inbox_dir(agent_id), f"{msg_id}.json")


def save_to_inbox(agent_id, msg):
    """将消息写入目标 Agent 的收件箱"""
    _ensure_dirs()
    path = _inbox_path(agent_id, msg['msg_id'])
    lock_path = os.path.join(_inbox_dir(agent_id), '.lock_inbox')
    with FileLock(lock_path, timeout=5):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(msg, f, ensure_ascii=False, indent=2)


def get_inbox(agent_id, status_filter=None):
    """
    获取 Agent 收件箱中的消息列表。

    :param status_filter: 过滤状态 (pending/delivered/read/processed)
    :return: 消息列表，按时间排序
    """
    inbox_d = _inbox_dir(agent_id)
    messages = []
    for fpath in sorted(glob.glob(os.path.join(inbox_d, 'MSG-*.json'))):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                msg = json.load(f)
            if status_filter and msg.get('status') != status_filter:
                continue
            messages.append(msg)
        except (json.JSONDecodeError, IOError):
            continue
    return messages


def get_message(agent_id, msg_id):
    """根据 ID 获取收件箱中的单条消息"""
    path = _inbox_path(agent_id, msg_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def update_message_status(agent_id, msg_id, new_status):
    """更新消息状态"""
    path = _inbox_path(agent_id, msg_id)
    lock_path = os.path.join(_inbox_dir(agent_id), '.lock_inbox')
    with FileLock(lock_path, timeout=5):
        if not os.path.exists(path):
            return False
        with open(path, 'r', encoding='utf-8') as f:
            msg = json.load(f)
        msg['status'] = new_status
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(msg, f, ensure_ascii=False, indent=2)
    return True


def count_inbox(agent_id, status_filter=None):
    """统计收件箱消息数量"""
    return len(get_inbox(agent_id, status_filter))


# ─── 会话线程操作 ──────────────────────────────────────────

def _conv_dir(task_id):
    d = os.path.join(CONV_DIR, task_id)
    os.makedirs(d, exist_ok=True)
    return d


def _thread_path(task_id):
    return os.path.join(_conv_dir(task_id), 'thread.json')


def append_to_thread(task_id, msg):
    """追加消息到任务会话线程"""
    _ensure_dirs()
    path = _thread_path(task_id)
    lock_path = os.path.join(_conv_dir(task_id), '.lock_thread')
    with FileLock(lock_path, timeout=5):
        thread = []
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    thread = json.load(f)
            except (json.JSONDecodeError, IOError):
                thread = []
        thread.append(msg)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(thread, f, ensure_ascii=False, indent=2)


def get_thread(task_id):
    """获取任务的完整会话线程"""
    path = _thread_path(task_id)
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def list_conversations():
    """列出所有有会话记录的任务 ID"""
    _ensure_dirs()
    result = []
    for d in sorted(os.listdir(CONV_DIR)):
        thread_path = os.path.join(CONV_DIR, d, 'thread.json')
        if os.path.isfile(thread_path):
            result.append(d)
    return result
