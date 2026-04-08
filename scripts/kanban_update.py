#!/usr/bin/env python3
"""
看板 CLI · 敕令状态机 + 数据清洗

帝王系统核心脚本：管理敕令（任务）的创建、状态流转、进度上报。
内置严格的状态机校验，非法状态跳转被拒绝并记录日志。

用法：
    python3 kanban_update.py create <id> "<标题>" <state> <org> <official>
    python3 kanban_update.py state <id> <state> "<说明>"
    python3 kanban_update.py flow <id> "<from>" "<to>" "<remark>"
    python3 kanban_update.py done <id> "<output>" "<summary>"
    python3 kanban_update.py progress <id> "<当前动态>" "<计划清单>"
    python3 kanban_update.py todo <id> <todo_id> "<title>" <status> [--detail "<详情>"]
    python3 kanban_update.py cancel <id> "<原因>"
    python3 kanban_update.py list [--state <state>] [--org <org>]
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone

# 确保能导入同目录模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from file_lock import locked_json_rw
from agent_registry import AGENT_DEPARTMENTS

# ─── 数据路径 ───────────────────────────────────────────────
REPO_DIR = os.environ.get('REPO_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(REPO_DIR, 'data')
TASKS_FILE = os.path.join(DATA_DIR, 'tasks_source.json')
LOG_FILE = os.path.join(DATA_DIR, 'kanban_audit.log')

os.makedirs(DATA_DIR, exist_ok=True)

# ─── 敕令状态定义 ───────────────────────────────────────────
STATES = {
    'Imperial':       '皇帝下旨',
    'ZhongshuDraft':  '中书起草',
    'ZhongshuReview': '中书内审',
    'MenxiaReview':   '门下审议',
    'Rejected':       '门下封驳',
    'Approved':       '准奏通过',
    'Dispatching':    '尚书派发',
    'Executing':      '执行中',
    'Review':         '待审查',
    'Done':           '已完成',
    'Cancelled':      '已取消',
    'Blocked':        '阻塞',
}

# ─── 合法状态转换 ───────────────────────────────────────────
_VALID_TRANSITIONS = {
    'Imperial':       ['ZhongshuDraft'],
    'ZhongshuDraft':  ['ZhongshuReview', 'MenxiaReview'],
    'ZhongshuReview': ['MenxiaReview', 'ZhongshuDraft'],
    'MenxiaReview':   ['Approved', 'Rejected', 'ZhongshuDraft'],
    'Rejected':       ['ZhongshuDraft'],
    'Approved':       ['Dispatching'],
    'Dispatching':    ['Executing'],
    'Executing':      ['Review', 'Done', 'Blocked'],
    'Review':         ['Done', 'Executing', 'Blocked'],
    'Done':           [],
    'Cancelled':      [],
    'Blocked':        ['Executing', 'Cancelled'],
}

# 任何状态都可以转到 Cancelled（除了已完成和已取消）
for st in STATES:
    if st not in ('Done', 'Cancelled') and 'Cancelled' not in _VALID_TRANSITIONS.get(st, []):
        _VALID_TRANSITIONS.setdefault(st, []).append('Cancelled')

# ─── 部门映射（来自共享模块）─────────────────────────────────
DEPARTMENTS = AGENT_DEPARTMENTS

# ─── 辅助函数 ───────────────────────────────────────────────

def now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def audit_log(msg):
    """追加审计日志"""
    ts = now_iso()
    line = f"[{ts}] {msg}\n"
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        pass


def clean_title(raw_title):
    """
    数据清洗：标题自动剥离文件路径、元数据、无效前缀。
    """
    title = raw_title.strip()
    # 去除文件路径
    title = re.sub(r'(/[a-zA-Z0-9_./-]+)+', '', title)
    # 去除 URL
    title = re.sub(r'https?://\S+', '', title)
    # 去除 JSON 元数据标记
    title = re.sub(r'\{[^}]*\}', '', title)
    # 去除多余空白
    title = re.sub(r'\s+', ' ', title).strip()
    # 限制长度
    if len(title) > 60:
        title = title[:57] + '...'
    return title or raw_title[:60]


def validate_transition(current_state, next_state):
    """校验状态转换合法性"""
    valid = _VALID_TRANSITIONS.get(current_state, [])
    if next_state not in valid:
        return False, f"非法状态转换: {current_state} → {next_state} (合法目标: {valid})"
    return True, ""


def find_task(tasks, task_id):
    """根据 ID 查找任务"""
    for i, t in enumerate(tasks):
        if t.get('id') == task_id:
            return i, t
    return -1, None


def print_ok(msg):
    print(f"\033[0;32m✅ {msg}\033[0m")


def print_err(msg):
    print(f"\033[0;31m❌ {msg}\033[0m", file=sys.stderr)


def print_info(msg):
    print(f"\033[0;34mℹ️  {msg}\033[0m")


# ─── 命令实现 ───────────────────────────────────────────────

def cmd_create(args):
    """创建新敕令"""
    if len(args) < 5:
        print_err("用法: create <id> <标题> <state> <org> <official>")
        sys.exit(1)

    task_id, raw_title, state, org, official = args[0], args[1], args[2], args[3], args[4]
    title = clean_title(raw_title)

    if state not in STATES:
        print_err(f"未知状态: {state} (可选: {list(STATES.keys())})")
        sys.exit(1)

    with locked_json_rw(TASKS_FILE) as (tasks, save):
        # 检查重复
        idx, existing = find_task(tasks, task_id)
        if existing:
            print_err(f"任务已存在: {task_id}，请使用 state 命令更新")
            sys.exit(1)

        task = {
            'id': task_id,
            'title': title,
            'official': official,
            'org': org,
            'state': state,
            'now': f'{official}已接旨',
            'eta': '-',
            'block': '无',
            'output': '',
            'ac': '',
            'progress': '',
            'plan': '',
            'todos': [],
            'flow_log': [
                {
                    'at': now_iso(),
                    'from': '皇上',
                    'to': org,
                    'remark': f'🏛️ 敕令创建: {title}',
                }
            ],
            'created_at': now_iso(),
            'updated_at': now_iso(),
        }
        tasks.append(task)
        save(tasks)

    audit_log(f"CREATE {task_id} | {title} | {state} | {org} | {official}")
    print_ok(f"敕令已创建: {task_id} | {title} | {STATES[state]}")


def cmd_state(args):
    """更新敕令状态"""
    if len(args) < 3:
        print_err("用法: state <id> <state> <说明>")
        sys.exit(1)

    task_id, next_state, remark = args[0], args[1], args[2]

    if next_state not in STATES:
        print_err(f"未知状态: {next_state}")
        sys.exit(1)

    with locked_json_rw(TASKS_FILE) as (tasks, save):
        idx, task = find_task(tasks, task_id)
        if task is None:
            print_err(f"敕令不存在: {task_id}")
            sys.exit(1)

        current = task['state']

        # 已完成的任务不能修改状态
        if current == 'Done':
            print_err(f"敕令已完成，不可修改状态: {task_id}")
            audit_log(f"REJECT state {task_id} | {current} → {next_state} | 已完成保护")
            sys.exit(1)

        ok, err_msg = validate_transition(current, next_state)
        if not ok:
            print_err(err_msg)
            audit_log(f"REJECT state {task_id} | {err_msg}")
            sys.exit(1)

        task['state'] = next_state
        task['now'] = remark
        task['updated_at'] = now_iso()
        tasks[idx] = task
        save(tasks)

    audit_log(f"STATE {task_id} | {current} → {next_state} | {remark}")
    print_ok(f"状态更新: {task_id} | {STATES[current]} → {STATES[next_state]}")


def cmd_flow(args):
    """记录敕令流转"""
    if len(args) < 4:
        print_err("用法: flow <id> <from> <to> <remark>")
        sys.exit(1)

    task_id, from_who, to_who, remark = args[0], args[1], args[2], args[3]

    with locked_json_rw(TASKS_FILE) as (tasks, save):
        idx, task = find_task(tasks, task_id)
        if task is None:
            print_err(f"敕令不存在: {task_id}")
            sys.exit(1)

        flow_entry = {
            'at': now_iso(),
            'from': from_who,
            'to': to_who,
            'remark': remark,
        }
        task.setdefault('flow_log', []).append(flow_entry)
        task['updated_at'] = now_iso()
        tasks[idx] = task
        save(tasks)

    audit_log(f"FLOW {task_id} | {from_who} → {to_who} | {remark}")
    print_ok(f"流转记录: {task_id} | {from_who} → {to_who}")


def cmd_done(args):
    """完成敕令"""
    if len(args) < 3:
        print_err("用法: done <id> <output> <summary>")
        sys.exit(1)

    task_id, output, summary = args[0], args[1], args[2]

    with locked_json_rw(TASKS_FILE) as (tasks, save):
        idx, task = find_task(tasks, task_id)
        if task is None:
            print_err(f"敕令不存在: {task_id}")
            sys.exit(1)

        current = task['state']
        if current == 'Done':
            print_err(f"敕令已完成: {task_id}")
            sys.exit(1)

        # done 允许从 Executing / Review 直接完成
        if current not in ('Executing', 'Review', 'Dispatching'):
            ok, err_msg = validate_transition(current, 'Done')
            if not ok:
                print_err(err_msg)
                audit_log(f"REJECT done {task_id} | {err_msg}")
                sys.exit(1)

        task['state'] = 'Done'
        task['output'] = output
        task['now'] = summary
        task['updated_at'] = now_iso()
        task.setdefault('flow_log', []).append({
            'at': now_iso(),
            'from': task.get('org', '未知'),
            'to': '皇上',
            'remark': f'✅ 回奏: {summary}',
        })
        tasks[idx] = task
        save(tasks)

    audit_log(f"DONE {task_id} | {summary}")
    print_ok(f"敕令完成: {task_id} | {summary}")


def cmd_progress(args):
    """更新实时进展"""
    if len(args) < 3:
        print_err("用法: progress <id> <当前动态> <计划清单>")
        sys.exit(1)

    task_id, progress_text, plan_text = args[0], args[1], args[2]

    with locked_json_rw(TASKS_FILE) as (tasks, save):
        idx, task = find_task(tasks, task_id)
        if task is None:
            print_err(f"敕令不存在: {task_id}")
            sys.exit(1)

        task['progress'] = progress_text
        task['plan'] = plan_text
        task['updated_at'] = now_iso()
        tasks[idx] = task
        save(tasks)

    audit_log(f"PROGRESS {task_id} | {progress_text}")
    print_ok(f"进展更新: {task_id}")


def cmd_todo(args):
    """子任务详情上报"""
    if len(args) < 4:
        print_err("用法: todo <id> <todo_id> <title> <status> [--detail <详情>]")
        sys.exit(1)

    task_id = args[0]
    todo_id = args[1]
    title = args[2]
    status = args[3]

    detail = ''
    if '--detail' in args:
        detail_idx = args.index('--detail')
        if detail_idx + 1 < len(args):
            detail = args[detail_idx + 1]

    if status not in ('pending', 'doing', 'completed', 'blocked'):
        print_err(f"未知子任务状态: {status} (可选: pending/doing/completed/blocked)")
        sys.exit(1)

    with locked_json_rw(TASKS_FILE) as (tasks, save):
        idx, task = find_task(tasks, task_id)
        if task is None:
            print_err(f"敕令不存在: {task_id}")
            sys.exit(1)

        todos = task.setdefault('todos', [])
        # 查找已有子任务
        found = False
        for t in todos:
            if str(t.get('id')) == str(todo_id):
                t['title'] = title
                t['status'] = status
                t['detail'] = detail
                t['updated_at'] = now_iso()
                found = True
                break

        if not found:
            todos.append({
                'id': todo_id,
                'title': title,
                'status': status,
                'detail': detail,
                'created_at': now_iso(),
                'updated_at': now_iso(),
            })

        task['updated_at'] = now_iso()
        tasks[idx] = task
        save(tasks)

    audit_log(f"TODO {task_id}/{todo_id} | {title} | {status}")
    print_ok(f"子任务更新: {task_id}/{todo_id} | {title} | {status}")


def cmd_cancel(args):
    """取消敕令"""
    if len(args) < 2:
        print_err("用法: cancel <id> <原因>")
        sys.exit(1)

    task_id, reason = args[0], args[1]

    with locked_json_rw(TASKS_FILE) as (tasks, save):
        idx, task = find_task(tasks, task_id)
        if task is None:
            print_err(f"敕令不存在: {task_id}")
            sys.exit(1)

        current = task['state']
        if current in ('Done', 'Cancelled'):
            print_err(f"敕令已{STATES[current]}，不可取消: {task_id}")
            sys.exit(1)

        task['state'] = 'Cancelled'
        task['now'] = f'已取消: {reason}'
        task['updated_at'] = now_iso()
        task.setdefault('flow_log', []).append({
            'at': now_iso(),
            'from': '系统',
            'to': '归档',
            'remark': f'🚫 取消: {reason}',
        })
        tasks[idx] = task
        save(tasks)

    audit_log(f"CANCEL {task_id} | {reason}")
    print_ok(f"敕令已取消: {task_id} | {reason}")


def cmd_list(args):
    """列出敕令"""
    state_filter = None
    org_filter = None
    i = 0
    while i < len(args):
        if args[i] == '--state' and i + 1 < len(args):
            state_filter = args[i + 1]
            i += 2
        elif args[i] == '--org' and i + 1 < len(args):
            org_filter = args[i + 1]
            i += 2
        else:
            i += 1

    if not os.path.exists(TASKS_FILE):
        print_info("暂无敕令")
        return

    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    if state_filter:
        tasks = [t for t in tasks if t.get('state') == state_filter]
    if org_filter:
        tasks = [t for t in tasks if t.get('org') == org_filter]

    if not tasks:
        print_info("无匹配敕令")
        return

    for t in tasks:
        state_label = STATES.get(t.get('state', ''), t.get('state', ''))
        print(f"  [{state_label}] {t['id']} | {t.get('title', '')} | {t.get('org', '')} | {t.get('official', '')}")


# ─── 主入口 ─────────────────────────────────────────────────

COMMANDS = {
    'create': cmd_create,
    'state': cmd_state,
    'flow': cmd_flow,
    'done': cmd_done,
    'progress': cmd_progress,
    'todo': cmd_todo,
    'cancel': cmd_cancel,
    'list': cmd_list,
}


def main():
    if len(sys.argv) < 2:
        print_err(f"用法: {sys.argv[0]} <command> [args...]")
        print_err(f"可用命令: {', '.join(COMMANDS.keys())}")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print_err(f"未知命令: {cmd}")
        print_err(f"可用命令: {', '.join(COMMANDS.keys())}")
        sys.exit(1)

    COMMANDS[cmd](sys.argv[2:])


if __name__ == '__main__':
    main()
