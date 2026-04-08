#!/usr/bin/env python3
"""
结构化任务调度 · 尚书令专用

将敕令子任务以结构化方式派发给指定部门 agent，并自动在看板中创建子任务记录。
子 agent 完成后通过 report 命令回报结果，自动更新看板状态。

用法：
    # 尚书令派发子任务
    python3 task_dispatch.py dispatch <敕令ID> <agent_id> "<任务描述>" "<验收标准>"

    # 子 agent 回报完成
    python3 task_dispatch.py report <敕令ID> <子任务序号> "<执行结果>" "<产出物>"

    # 子 agent 回报失败/阻塞
    python3 task_dispatch.py report <敕令ID> <子任务序号> "<原因>" "" --status blocked

    # 查看敕令所有子任务状态
    python3 task_dispatch.py status <敕令ID>

作者：XuJiaKai
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from file_lock import locked_json_rw
from agent_registry import AGENT_DEPARTMENTS, AGENT_LABELS
from agent_heartbeat import pulse as heartbeat_pulse

REPO_DIR = os.environ.get('REPO_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(REPO_DIR, 'data')
TASKS_FILE = os.path.join(DATA_DIR, 'tasks_source.json')
DISPATCH_FILE = os.path.join(DATA_DIR, 'dispatch_log.json')
LOG_FILE = os.path.join(DATA_DIR, 'kanban_audit.log')

os.makedirs(DATA_DIR, exist_ok=True)


def now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def audit_log(msg):
    ts = now_iso()
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


def print_ok(msg):
    print(f"\033[0;32m✅ {msg}\033[0m")


def print_err(msg):
    print(f"\033[0;31m❌ {msg}\033[0m", file=sys.stderr)


def print_info(msg):
    print(f"\033[0;34mℹ️  {msg}\033[0m")


def load_dispatch_log():
    """加载派发日志（带文件锁保护）"""
    from file_lock import FileLock
    lock_path = os.path.join(DATA_DIR, '.lock_dispatch_log.json')
    with FileLock(lock_path, timeout=5):
        if os.path.exists(DISPATCH_FILE):
            with open(DISPATCH_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    return {}


def save_dispatch_log(data):
    """保存派发日志（带文件锁保护）"""
    from file_lock import FileLock
    lock_path = os.path.join(DATA_DIR, '.lock_dispatch_log.json')
    with FileLock(lock_path, timeout=5):
        tmp = DISPATCH_FILE + f'.tmp-{os.getpid()}'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DISPATCH_FILE)


# ─── dispatch: 尚书令派发子任务 ───────────────────────────
def cmd_dispatch(args):
    if len(args) < 4:
        print_err("用法: dispatch <敕令ID> <agent_id> \"<任务描述>\" \"<验收标准>\"")
        sys.exit(1)

    task_id, agent_id, description, acceptance = args[0], args[1], args[2], args[3]

    if agent_id not in AGENT_DEPARTMENTS:
        print_err(f"未知 agent: {agent_id} (可选: {list(AGENT_DEPARTMENTS.keys())})")
        sys.exit(1)

    # 1. 在 dispatch_log 中记录
    log = load_dispatch_log()
    subtasks = log.setdefault(task_id, [])
    seq = len(subtasks) + 1
    subtask_id = f"{task_id}-S{seq}"

    entry = {
        'subtask_id': subtask_id,
        'seq': seq,
        'agent_id': agent_id,
        'department': AGENT_DEPARTMENTS[agent_id],
        'description': description,
        'acceptance': acceptance,
        'status': 'dispatched',
        'result': '',
        'output': '',
        'dispatched_at': now_iso(),
        'completed_at': '',
    }
    subtasks.append(entry)
    save_dispatch_log(log)

    # 2. 在看板主任务中添加 todo
    with locked_json_rw(TASKS_FILE) as (tasks, save):
        for t in tasks:
            if t.get('id') == task_id:
                t.setdefault('todos', []).append({
                    'id': subtask_id,
                    'title': f"[{AGENT_DEPARTMENTS[agent_id]}] {description}",
                    'status': 'doing',
                    'detail': f"验收标准: {acceptance}",
                    'created_at': now_iso(),
                    'updated_at': now_iso(),
                })
                t['updated_at'] = now_iso()
                save(tasks)
                break
        else:
            print_err(f"敕令不存在: {task_id}（请先用 kanban_update.py create 创建）")
            sys.exit(1)

    audit_log(f"DISPATCH {subtask_id} | {agent_id} | {description}")
    # 心跳：标记目标 agent 为 waiting
    try:
        heartbeat_pulse(agent_id, status='waiting', task=description,
                        edict=task_id, phase='等待派令', tool='script')
    except Exception:
        pass
    print_ok(f"子任务已派发: {subtask_id} → {AGENT_DEPARTMENTS[agent_id]}({agent_id})")
    print_info(f"任务: {description}")
    print_info(f"验收: {acceptance}")

    # 3. 输出供尚书令发给子 agent 的结构化派令
    print()
    print("── 派令模板（复制发给子 agent）──")
    print(f"【派令】{subtask_id}")
    print(f"【敕令】{task_id}")
    print(f"【任务描述】{description}")
    print(f"【验收标准】{acceptance}")
    print(f"【完成后执行】python3 {REPO_DIR}/scripts/task_dispatch.py report {task_id} {seq} \"<执行结果>\" \"<产出物>\"")
    print("── 派令结束 ──")


# ─── report: 子 agent 回报结果 ────────────────────────────
def cmd_report(args):
    if len(args) < 4:
        print_err("用法: report <敕令ID> <子任务序号> \"<执行结果>\" \"<产出物>\" [--status blocked]")
        sys.exit(1)

    task_id, seq_str, result, output = args[0], args[1], args[2], args[3]

    status = 'completed'
    if '--status' in args:
        idx = args.index('--status')
        if idx + 1 < len(args):
            status = args[idx + 1]
    if status not in ('completed', 'blocked', 'failed'):
        print_err(f"未知状态: {status} (可选: completed/blocked/failed)")
        sys.exit(1)

    try:
        seq = int(seq_str)
    except ValueError:
        print_err(f"子任务序号必须是数字: {seq_str}")
        sys.exit(1)

    # 1. 更新 dispatch_log
    log = load_dispatch_log()
    subtasks = log.get(task_id, [])
    found = None
    for st in subtasks:
        if st['seq'] == seq:
            found = st
            break

    if not found:
        print_err(f"子任务不存在: {task_id} 序号 {seq}")
        sys.exit(1)

    found['status'] = status
    found['result'] = result
    found['output'] = output
    found['completed_at'] = now_iso()
    save_dispatch_log(log)

    subtask_id = found['subtask_id']

    # 2. 更新看板 todo 状态
    todo_status = 'completed' if status == 'completed' else 'blocked'
    with locked_json_rw(TASKS_FILE) as (tasks, save):
        for t in tasks:
            if t.get('id') == task_id:
                for todo in t.get('todos', []):
                    if todo.get('id') == subtask_id:
                        todo['status'] = todo_status
                        todo['detail'] = result
                        todo['updated_at'] = now_iso()
                        break
                t['updated_at'] = now_iso()
                save(tasks)
                break

    audit_log(f"REPORT {subtask_id} | {status} | {result}")
    # 心跳：标记回报 agent 为 done/blocked
    report_agent = found.get('agent_id', '')
    if report_agent:
        try:
            hb_status = 'done' if status == 'completed' else 'blocked'
            heartbeat_pulse(report_agent, status=hb_status, task=result,
                            edict=task_id, phase='已回报', tool='script')
        except Exception:
            pass
    print_ok(f"子任务回报: {subtask_id} | {status}")

    # 3. 检查是否全部完成
    total = len(subtasks)
    done = sum(1 for s in subtasks if s['status'] in ('completed', 'failed'))
    blocked = sum(1 for s in subtasks if s['status'] == 'blocked')

    if done + blocked == total:
        if blocked > 0:
            print_info(f"⚠️ 敕令 {task_id} 所有子任务已回报，但有 {blocked} 个阻塞")
        else:
            print_ok(f"🎉 敕令 {task_id} 所有 {total} 个子任务已完成！尚书令可以汇总回报了。")
    else:
        print_info(f"进度: {done}/{total} 完成, {blocked} 阻塞, {total - done - blocked} 执行中")


# ─── status: 查看子任务状态 ───────────────────────────────
def cmd_status(args):
    if len(args) < 1:
        print_err("用法: status <敕令ID>")
        sys.exit(1)

    task_id = args[0]
    log = load_dispatch_log()
    subtasks = log.get(task_id, [])

    if not subtasks:
        print_info(f"敕令 {task_id} 暂无派发记录")
        return

    status_icons = {
        'dispatched': '🔄',
        'completed': '✅',
        'blocked': '🚫',
        'failed': '❌',
    }

    total = len(subtasks)
    done = sum(1 for s in subtasks if s['status'] == 'completed')
    print(f"\n📋 敕令 {task_id} 子任务状态 ({done}/{total} 完成)\n")
    print(f"{'序号':<6} {'状态':<4} {'部门':<10} {'Agent':<14} {'任务描述'}")
    print("─" * 70)
    for st in subtasks:
        icon = status_icons.get(st['status'], '?')
        print(f"  {st['seq']:<4} {icon}  {st['department']:<8} {st['agent_id']:<12} {st['description'][:40]}")
        if st['result']:
            print(f"       └─ {st['result'][:60]}")
    print()


# ─── 主入口 ───────────────────────────────────────────────
COMMANDS = {
    'dispatch': cmd_dispatch,
    'report': cmd_report,
    'status': cmd_status,
}


def main():
    if len(sys.argv) < 2:
        print_err(f"用法: {sys.argv[0]} <command> [args...]")
        print_err(f"可用命令: {', '.join(COMMANDS.keys())}")
        print_err("")
        print_err("  dispatch  <敕令ID> <agent_id> \"<任务>\" \"<验收标准>\"  - 派发子任务")
        print_err("  report    <敕令ID> <序号> \"<结果>\" \"<产出>\"          - 回报结果")
        print_err("  status    <敕令ID>                                    - 查看子任务状态")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print_err(f"未知命令: {cmd}")
        sys.exit(1)

    COMMANDS[cmd](sys.argv[2:])


if __name__ == '__main__':
    main()
