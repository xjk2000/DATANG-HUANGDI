#!/usr/bin/env python3
"""
帝王系统 · Agent 心跳状态管理

提供 Claude Code CLI 和 OpenClaw 共享的 Agent 实时状态文件。
任何一方都可以读写 data/agent_heartbeat.json，实现跨工具协作可见性。

用法:
  python3 agent_heartbeat.py pulse <agent_id> --status working --task "描述" [选项]
  python3 agent_heartbeat.py status [--agent <agent_id>] [--format json|table]
  python3 agent_heartbeat.py check [--timeout <秒>]
  python3 agent_heartbeat.py clear <agent_id>

选项:
  --edict <敕令ID>     关联的敕令
  --phase <阶段>       当前执行阶段
  --tool <工具名>      来源工具 (claude-code / openclaw / script)
  --detail <详情>      额外详情

作者: XuJiaKai
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from file_lock import locked_json_rw
from agent_registry import ALL_AGENT_IDS, AGENT_NAMES, get_agent_name

# ─── 路径 ───────────────────────────────────────────────────
REPO_DIR = os.environ.get('REPO_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(REPO_DIR, 'data')
HEARTBEAT_FILE = os.path.join(DATA_DIR, 'agent_heartbeat.json')

os.makedirs(DATA_DIR, exist_ok=True)

# ─── 状态常量 ────────────────────────────────────────────────
VALID_STATUSES = {'idle', 'working', 'blocked', 'done', 'error', 'waiting'}

STATUS_LABELS = {
    'idle':    '💤 空闲',
    'working': '⚙️ 执行中',
    'blocked': '🚧 阻塞',
    'done':    '✅ 已完成',
    'error':   '❌ 异常',
    'waiting': '⏳ 等待中',
}

# 超时阈值（秒）
DEFAULT_TIMEOUT = 600  # 10 分钟无心跳视为卡死
WARNING_TIMEOUT = 300  # 5 分钟无心跳视为可疑


# ─── 辅助函数 ────────────────────────────────────────────────

def now_iso():
    """返回当前 UTC 时间 ISO 格式"""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def load_heartbeat():
    """加载心跳文件"""
    if os.path.exists(HEARTBEAT_FILE):
        try:
            with open(HEARTBEAT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_heartbeat(data):
    """保存心跳文件（原子写入）"""
    tmp = HEARTBEAT_FILE + f'.tmp-{os.getpid()}'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, HEARTBEAT_FILE)


def parse_iso(iso_str):
    """解析 ISO 时间字符串为 datetime"""
    try:
        return datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


def seconds_since(iso_str):
    """计算距今秒数"""
    dt = parse_iso(iso_str)
    if not dt:
        return float('inf')
    return (datetime.now(timezone.utc) - dt).total_seconds()


# ─── 核心 API（供其他脚本 import 使用）────────────────────────

def pulse(agent_id, status='working', task='', edict='', phase='',
          tool='script', detail=''):
    """
    上报 Agent 心跳。

    供其他脚本直接调用：
        from agent_heartbeat import pulse
        pulse('jiangzuo', status='working', task='编写用户认证模块', edict='CL-001')
    """
    data = load_heartbeat()

    entry = data.get(agent_id, {})
    now = now_iso()

    # 如果从 idle/done/error 切到 working，记录开始时间
    prev_status = entry.get('status', 'idle')
    if status == 'working' and prev_status != 'working':
        entry['started_at'] = now

    entry.update({
        'agent_id': agent_id,
        'agent_name': get_agent_name(agent_id),
        'status': status,
        'updated_at': now,
        'pid': os.getpid(),
    })

    if task:
        entry['task'] = task
    if edict:
        entry['edict'] = edict
    if phase:
        entry['phase'] = phase
    if tool:
        entry['tool'] = tool
    if detail:
        entry['detail'] = detail

    # 如果完成/空闲，清理开始时间
    if status in ('idle', 'done'):
        entry.pop('started_at', None)
        entry.pop('task', None)
        entry.pop('phase', None)
        entry.pop('detail', None)

    data[agent_id] = entry
    save_heartbeat(data)
    return entry


def get_status(agent_id=None):
    """
    查询 Agent 状态。

    agent_id=None 时返回全部，指定时返回单个。
    """
    data = load_heartbeat()
    if agent_id:
        return data.get(agent_id)
    return data


def check_stuck(timeout=DEFAULT_TIMEOUT):
    """
    检测卡死的 Agent。

    返回: [(agent_id, entry, elapsed_seconds), ...]
    """
    data = load_heartbeat()
    stuck = []
    for agent_id, entry in data.items():
        if entry.get('status') not in ('working', 'blocked', 'waiting'):
            continue
        elapsed = seconds_since(entry.get('updated_at', ''))
        if elapsed > timeout:
            stuck.append((agent_id, entry, elapsed))
    stuck.sort(key=lambda x: x[2], reverse=True)
    return stuck


def clear_agent(agent_id):
    """清除指定 Agent 的心跳记录"""
    data = load_heartbeat()
    if agent_id in data:
        del data[agent_id]
        save_heartbeat(data)
        return True
    return False


# ─── CLI 命令 ────────────────────────────────────────────────

def cmd_pulse(args):
    """上报心跳"""
    if not args:
        print('用法: agent_heartbeat.py pulse <agent_id> [选项]')
        print('选项:')
        print('  --status <状态>    idle|working|blocked|done|error|waiting')
        print('  --task "<描述>"    当前任务描述')
        print('  --edict <敕令ID>  关联敕令')
        print('  --phase "<阶段>"  执行阶段')
        print('  --tool <工具>     来源 (claude-code|openclaw|script)')
        print('  --detail "<详情>" 额外信息')
        sys.exit(1)

    agent_id = args[0]
    if agent_id not in set(ALL_AGENT_IDS):
        print(f'❌ 未知 Agent: {agent_id}')
        sys.exit(1)

    # 解析选项
    opts = {}
    i = 1
    while i < len(args):
        if args[i] == '--status' and i + 1 < len(args):
            opts['status'] = args[i + 1]
            i += 2
        elif args[i] == '--task' and i + 1 < len(args):
            opts['task'] = args[i + 1]
            i += 2
        elif args[i] == '--edict' and i + 1 < len(args):
            opts['edict'] = args[i + 1]
            i += 2
        elif args[i] == '--phase' and i + 1 < len(args):
            opts['phase'] = args[i + 1]
            i += 2
        elif args[i] == '--tool' and i + 1 < len(args):
            opts['tool'] = args[i + 1]
            i += 2
        elif args[i] == '--detail' and i + 1 < len(args):
            opts['detail'] = args[i + 1]
            i += 2
        else:
            print(f'❌ 未知选项: {args[i]}')
            sys.exit(1)

    status = opts.get('status', 'working')
    if status not in VALID_STATUSES:
        print(f'❌ 无效状态: {status}  (可选: {", ".join(sorted(VALID_STATUSES))})')
        sys.exit(1)

    entry = pulse(agent_id, **opts)
    name = entry.get('agent_name', agent_id)
    label = STATUS_LABELS.get(status, status)
    print(f'💓 {name} ({agent_id}) → {label}')
    if entry.get('task'):
        print(f'   📋 {entry["task"]}')
    if entry.get('edict'):
        print(f'   📜 敕令: {entry["edict"]}')


def cmd_status(args):
    """查看 Agent 状态"""
    # 解析选项
    agent_filter = None
    fmt = 'table'
    i = 0
    while i < len(args):
        if args[i] == '--agent' and i + 1 < len(args):
            agent_filter = args[i + 1]
            i += 2
        elif args[i] == '--format' and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1

    data = get_status(agent_filter)

    if fmt == 'json':
        print(json.dumps(data if data else {}, ensure_ascii=False, indent=2))
        return

    # 表格输出
    if agent_filter:
        if not data:
            print(f'ℹ️  {agent_filter} 无心跳记录')
            return
        _print_entry(agent_filter, data)
        return

    if not data:
        print('ℹ️  暂无 Agent 心跳记录')
        return

    print(f'{"─" * 70}')
    print(f'  {"Agent":<18} {"状态":<10} {"任务":<25} {"更新时间"}')
    print(f'{"─" * 70}')
    for agent_id in ALL_AGENT_IDS:
        if agent_id not in data:
            continue
        entry = data[agent_id]
        name = entry.get('agent_name', agent_id)
        status = STATUS_LABELS.get(entry.get('status', ''), entry.get('status', '?'))
        task = entry.get('task', '-')
        if len(task) > 22:
            task = task[:20] + '..'
        updated = entry.get('updated_at', '-')
        if updated != '-':
            updated = updated[11:19]  # HH:MM:SS
        elapsed = seconds_since(entry.get('updated_at', ''))
        timeout_mark = ''
        if entry.get('status') in ('working', 'blocked', 'waiting'):
            if elapsed > DEFAULT_TIMEOUT:
                timeout_mark = ' ⚠️卡死'
            elif elapsed > WARNING_TIMEOUT:
                timeout_mark = ' ⏰'
        print(f'  {name:<16} {status:<8} {task:<25} {updated}{timeout_mark}')
    print(f'{"─" * 70}')


def _print_entry(agent_id, entry):
    """打印单个 Agent 详情"""
    name = entry.get('agent_name', agent_id)
    status = STATUS_LABELS.get(entry.get('status', ''), entry.get('status', ''))
    print(f'Agent:    {name} ({agent_id})')
    print(f'状态:     {status}')
    if entry.get('task'):
        print(f'任务:     {entry["task"]}')
    if entry.get('edict'):
        print(f'敕令:     {entry["edict"]}')
    if entry.get('phase'):
        print(f'阶段:     {entry["phase"]}')
    if entry.get('tool'):
        print(f'工具:     {entry["tool"]}')
    if entry.get('started_at'):
        elapsed = seconds_since(entry['started_at'])
        mins = int(elapsed // 60)
        print(f'已执行:   {mins} 分钟')
    if entry.get('updated_at'):
        elapsed = seconds_since(entry['updated_at'])
        print(f'最后心跳: {entry["updated_at"]} ({int(elapsed)}秒前)')
    if entry.get('pid'):
        print(f'PID:      {entry["pid"]}')


def cmd_check(args):
    """检测卡死 Agent"""
    timeout = DEFAULT_TIMEOUT
    i = 0
    while i < len(args):
        if args[i] == '--timeout' and i + 1 < len(args):
            timeout = int(args[i + 1])
            i += 2
        else:
            i += 1

    stuck = check_stuck(timeout)

    if not stuck:
        print('✅ 所有活跃 Agent 运行正常，无卡死检测')
        sys.exit(0)

    print(f'⚠️  检测到 {len(stuck)} 个可能卡死的 Agent:')
    print()
    for agent_id, entry, elapsed in stuck:
        name = entry.get('agent_name', agent_id)
        mins = int(elapsed // 60)
        task = entry.get('task', '未知任务')
        edict = entry.get('edict', '-')
        tool = entry.get('tool', '-')
        print(f'  🚨 {name} ({agent_id})')
        print(f'     最后心跳: {mins} 分钟前')
        print(f'     任务: {task}')
        print(f'     敕令: {edict} | 工具: {tool}')
        print()

    # 退出码 1 表示有卡死 agent，可供 CI/脚本判断
    sys.exit(1)


def cmd_clear(args):
    """清除 Agent 心跳"""
    if not args:
        print('用法: agent_heartbeat.py clear <agent_id>')
        sys.exit(1)
    agent_id = args[0]
    if clear_agent(agent_id):
        print(f'✅ 已清除 {get_agent_name(agent_id)} ({agent_id}) 的心跳记录')
    else:
        print(f'ℹ️  {agent_id} 无心跳记录')


# ─── 入口 ────────────────────────────────────────────────────

COMMANDS = {
    'pulse':  cmd_pulse,
    'status': cmd_status,
    'check':  cmd_check,
    'clear':  cmd_clear,
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print('帝王系统 · Agent 心跳状态管理')
        print()
        print('用法: python3 agent_heartbeat.py <命令> [参数]')
        print()
        print('命令:')
        print('  pulse   上报心跳（Agent 主动调用）')
        print('  status  查看所有 Agent 当前状态')
        print('  check   检测卡死 Agent（超时未心跳）')
        print('  clear   清除指定 Agent 心跳记录')
        print()
        print('示例:')
        print('  # Agent 开始工作时上报心跳')
        print('  python3 agent_heartbeat.py pulse jiangzuo --status working \\')
        print('    --task "实现用户认证" --edict CL-001 --tool claude-code')
        print()
        print('  # 查看所有 Agent 状态（Claude Code CLI 和 OpenClaw 都能看到）')
        print('  python3 agent_heartbeat.py status')
        print()
        print('  # 检测卡死 Agent')
        print('  python3 agent_heartbeat.py check --timeout 600')
        sys.exit(1)

    cmd = sys.argv[1]
    COMMANDS[cmd](sys.argv[2:])


if __name__ == '__main__':
    main()
