#!/usr/bin/env python3
"""
Agent 自建调度 · 帝王系统

不依赖 OpenClaw 的 subagents 通信机制，让 agent 通过调用此脚本唤起另一个 agent，
携带会话上下文和任务信息。管理系统通过 invoke_log.json 监控完整调度链路。

用法：
    # 唤起目标 agent 并传递任务（同步等待结果）
    python3 agent_invoke.py invoke <source_agent> <target_agent> "<任务描述>" [--context "<上下文>"] [--edict "<敕令ID>"]

    # 唤起目标 agent（异步后台执行，不等待结果）
    python3 agent_invoke.py invoke <source_agent> <target_agent> "<任务描述>" --async

    # 查看某个敕令的调度链路
    python3 agent_invoke.py chain <敕令ID>

    # 查看最近 N 条调度日志
    python3 agent_invoke.py log [--limit N]

    # 查看某 agent 的调度历史
    python3 agent_invoke.py history <agent_id> [--limit N]

作者：XuJiaKai
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from file_lock import locked_json_rw, FileLock
from agent_registry import (
    VALID_AGENTS, AGENT_NAMES, AGENT_LABELS,
    INVOKE_PERMISSIONS, can_invoke, get_agent_name,
)

# ── 路径常量 ──────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(REPO_DIR, 'data')
INVOKE_LOG = os.path.join(DATA_DIR, 'invoke_log.json')
AUDIT_LOG = os.path.join(DATA_DIR, 'kanban_audit.log')


def now_iso():
    """返回 ISO 格式的 UTC 时间戳"""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def audit(msg):
    """写入审计日志"""
    os.makedirs(DATA_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(AUDIT_LOG, 'a', encoding='utf-8') as f:
        f.write(f'[{ts}] [agent_invoke] {msg}\n')


def _load_log():
    """加载调度日志（带文件锁保护）"""
    lock_path = os.path.join(DATA_DIR, '.lock_invoke_log.json')
    with FileLock(lock_path, timeout=5):
        if os.path.exists(INVOKE_LOG):
            with open(INVOKE_LOG, 'r', encoding='utf-8') as f:
                return json.load(f)
    return []


# ── invoke: 唤起目标 agent ────────────────────────────────────
def cmd_invoke(args):
    """唤起目标 agent 并传递任务"""
    if len(args) < 3:
        print('用法: agent_invoke.py invoke <source_agent> <target_agent> "<任务描述>" [选项]')
        print('选项:')
        print('  --context "<上下文>"   附加上下文信息')
        print('  --edict "<敕令ID>"     关联的敕令 ID')
        print('  --async               异步执行，不等待结果')
        sys.exit(1)

    source = args[0]
    target = args[1]
    task_desc = args[2]

    # 解析可选参数
    context = ''
    edict_id = ''
    is_async = False
    i = 3
    while i < len(args):
        if args[i] == '--context' and i + 1 < len(args):
            context = args[i + 1]
            i += 2
        elif args[i] == '--edict' and i + 1 < len(args):
            edict_id = args[i + 1]
            i += 2
        elif args[i] == '--async':
            is_async = True
            i += 1
        else:
            i += 1

    # 校验 agent ID
    if source not in VALID_AGENTS:
        print(f'❌ 无效的来源 Agent: {source}')
        print(f'   合法 Agent: {", ".join(sorted(VALID_AGENTS))}')
        sys.exit(1)

    if target not in VALID_AGENTS:
        print(f'❌ 无效的目标 Agent: {target}')
        print(f'   合法 Agent: {", ".join(sorted(VALID_AGENTS))}')
        sys.exit(1)

    # 校验调度权限
    if not can_invoke(source, target):
        allowed = INVOKE_PERMISSIONS.get(source, set())
        print(f'❌ 权限拒绝: {get_agent_name(source)} 无权唤起 {get_agent_name(target)}')
        if allowed:
            names = [f'{get_agent_name(a)}({a})' for a in sorted(allowed)]
            print(f'   允许唤起: {", ".join(names)}')
        else:
            print(f'   {get_agent_name(source)} 未配置调度权限')
        audit(f'DENIED {source} → {target} | 权限拒绝')
        sys.exit(1)

    # 生成调度 ID
    invoke_id = f'INV-{int(time.time())}-{os.getpid()}'

    # 构建传递给目标 agent 的 prompt
    prompt_parts = [
        f'【派令通知】来自 {AGENT_NAMES.get(source, source)}（{source}）',
    ]
    if edict_id:
        prompt_parts.append(f'关联敕令: {edict_id}')
    prompt_parts.append(f'调度ID: {invoke_id}')
    prompt_parts.append(f'')
    prompt_parts.append(f'## 任务')
    prompt_parts.append(task_desc)
    if context:
        prompt_parts.append(f'')
        prompt_parts.append(f'## 上下文')
        prompt_parts.append(context)
    prompt_parts.append(f'')
    prompt_parts.append(f'## 要求')
    prompt_parts.append(f'1. 开始执行时立即更新看板进度')
    prompt_parts.append(f'2. 完成后用 task_dispatch.py report 回报结果')
    prompt_parts.append(f'3. 如遇阻塞，立即回报阻塞原因')

    prompt = '\n'.join(prompt_parts)

    # 记录调度日志
    log_entry = {
        'invoke_id': invoke_id,
        'source': source,
        'source_name': AGENT_NAMES.get(source, source),
        'target': target,
        'target_name': AGENT_NAMES.get(target, target),
        'task': task_desc,
        'context': context,
        'edict_id': edict_id,
        'mode': 'async' if is_async else 'sync',
        'status': 'dispatched',
        'result': '',
        'created_at': now_iso(),
        'completed_at': '',
    }

    with locked_json_rw(INVOKE_LOG) as (data, save):
        data.append(log_entry)
        save(data)

    audit(f'{source} → {target} | {invoke_id} | {task_desc[:80]}')

    # 输出调度信息
    print(f'╔══════════════════════════════════════════════╗')
    print(f'║  📨 Agent 调度令                              ║')
    print(f'╚══════════════════════════════════════════════╝')
    print(f'  调度ID:   {invoke_id}')
    print(f'  来源:     {AGENT_NAMES.get(source, source)} ({source})')
    print(f'  目标:     {AGENT_NAMES.get(target, target)} ({target})')
    if edict_id:
        print(f'  敕令:     {edict_id}')
    print(f'  模式:     {"异步" if is_async else "同步"}')
    print(f'  任务:     {task_desc[:100]}')
    print()

    # 执行 openclaw chat 命令
    cmd = ['openclaw', 'chat', '--agent', target, '-p', prompt]

    if is_async:
        # 异步：后台执行
        log_file = os.path.join(DATA_DIR, f'invoke_{invoke_id}.log')
        with open(log_file, 'w', encoding='utf-8') as lf:
            proc = subprocess.Popen(
                cmd,
                stdout=lf,
                stderr=subprocess.STDOUT,
                cwd=REPO_DIR,
            )
        print(f'  ✅ 已异步启动 (PID: {proc.pid})')
        print(f'  📄 输出日志: {log_file}')

        # 更新日志
        with locked_json_rw(INVOKE_LOG) as (data, save):
            for entry in data:
                if entry['invoke_id'] == invoke_id:
                    entry['status'] = 'running'
                    entry['pid'] = proc.pid
                    entry['log_file'] = log_file
                    break
            save(data)
    else:
        # 同步：等待执行结果
        print(f'  ⏳ 正在执行，等待 {target} 响应...')
        print(f'  {"─" * 50}')
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 分钟超时
                cwd=REPO_DIR,
            )
            output = result.stdout.strip()
            if result.returncode == 0:
                print(f'  ✅ {target} 执行完成')
                print(f'  {"─" * 50}')
                if output:
                    # 截取输出（避免刷屏）
                    lines = output.split('\n')
                    if len(lines) > 30:
                        for line in lines[:15]:
                            print(f'  {line}')
                        print(f'  ... (省略 {len(lines) - 30} 行) ...')
                        for line in lines[-15:]:
                            print(f'  {line}')
                    else:
                        for line in lines:
                            print(f'  {line}')
                status = 'completed'
            else:
                print(f'  ❌ {target} 执行失败 (exit code: {result.returncode})')
                if result.stderr:
                    print(f'  错误: {result.stderr[:500]}')
                output = result.stderr or output
                status = 'failed'
        except subprocess.TimeoutExpired:
            print(f'  ⏰ {target} 执行超时（10分钟）')
            output = 'TIMEOUT'
            status = 'timeout'
        except FileNotFoundError:
            print(f'  ❌ 未找到 openclaw 命令，请确认已安装')
            print(f'  💡 提示: 可以手动在 {target} 的 workspace 中执行任务')
            output = 'openclaw not found'
            status = 'error'

        # 更新调度日志
        with locked_json_rw(INVOKE_LOG) as (data, save):
            for entry in data:
                if entry['invoke_id'] == invoke_id:
                    entry['status'] = status
                    entry['result'] = output[:2000] if output else ''
                    entry['completed_at'] = now_iso()
                    break
            save(data)

        audit(f'{invoke_id} → {status} | {target}')


# ── chain: 查看敕令调度链路 ───────────────────────────────────
def cmd_chain(args):
    """查看某个敕令的完整调度链路"""
    if len(args) < 1:
        print('用法: agent_invoke.py chain <敕令ID>')
        sys.exit(1)

    edict_id = args[0]
    data = _load_log()

    entries = [e for e in data if e.get('edict_id') == edict_id]
    if not entries:
        print(f'未找到敕令 {edict_id} 的调度记录')
        return

    print(f'╔══════════════════════════════════════════════╗')
    print(f'║  📋 敕令 {edict_id} 调度链路                 ║')
    print(f'╚══════════════════════════════════════════════╝')
    print()

    for i, e in enumerate(entries, 1):
        status_icon = {
            'dispatched': '📨',
            'running': '🔄',
            'completed': '✅',
            'failed': '❌',
            'timeout': '⏰',
            'error': '🚫',
        }.get(e['status'], '❓')

        print(f'  [{i}] {status_icon} {e["source_name"]} → {e["target_name"]}')
        print(f'      调度ID: {e["invoke_id"]}')
        print(f'      任务: {e["task"][:80]}')
        print(f'      状态: {e["status"]}')
        print(f'      时间: {e["created_at"]}')
        if e.get('completed_at'):
            print(f'      完成: {e["completed_at"]}')
        print()


# ── log: 查看最近调度日志 ─────────────────────────────────────
def cmd_log(args):
    """查看最近 N 条调度日志"""
    limit = 20
    i = 0
    while i < len(args):
        if args[i] == '--limit' and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        else:
            i += 1

    data = _load_log()
    entries = data[-limit:]

    if not entries:
        print('暂无调度记录')
        return

    print(f'╔══════════════════════════════════════════════╗')
    print(f'║  📋 最近 {len(entries)} 条调度记录              ║')
    print(f'╚══════════════════════════════════════════════╝')
    print()

    for e in entries:
        status_icon = {
            'dispatched': '📨',
            'running': '🔄',
            'completed': '✅',
            'failed': '❌',
            'timeout': '⏰',
            'error': '🚫',
        }.get(e['status'], '❓')

        edict_tag = f' [{e["edict_id"]}]' if e.get('edict_id') else ''
        print(f'  {status_icon} {e["invoke_id"]}{edict_tag}')
        print(f'     {e["source_name"]} → {e["target_name"]} | {e["task"][:60]}')
        print(f'     {e["created_at"]} | {e["status"]}')
        print()


# ── history: 查看某 agent 的调度历史 ──────────────────────────
def cmd_history(args):
    """查看某 agent 的调度历史"""
    if len(args) < 1:
        print('用法: agent_invoke.py history <agent_id> [--limit N]')
        sys.exit(1)

    agent_id = args[0]
    limit = 20
    i = 1
    while i < len(args):
        if args[i] == '--limit' and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        else:
            i += 1

    data = _load_log()
    entries = [e for e in data if e['source'] == agent_id or e['target'] == agent_id]
    entries = entries[-limit:]

    if not entries:
        print(f'未找到 {agent_id} 的调度记录')
        return

    agent_name = AGENT_NAMES.get(agent_id, agent_id)
    print(f'╔══════════════════════════════════════════════╗')
    print(f'║  📋 {agent_name}（{agent_id}）调度历史         ║')
    print(f'╚══════════════════════════════════════════════╝')
    print()

    for e in entries:
        status_icon = {
            'dispatched': '📨',
            'running': '🔄',
            'completed': '✅',
            'failed': '❌',
            'timeout': '⏰',
            'error': '🚫',
        }.get(e['status'], '❓')

        direction = '→' if e['source'] == agent_id else '←'
        other = e['target_name'] if e['source'] == agent_id else e['source_name']
        edict_tag = f' [{e["edict_id"]}]' if e.get('edict_id') else ''

        print(f'  {status_icon} {direction} {other}{edict_tag}')
        print(f'     {e["task"][:60]}')
        print(f'     {e["created_at"]} | {e["status"]}')
        print()


# ── main ──────────────────────────────────────────────────────
COMMANDS = {
    'invoke':  cmd_invoke,
    'chain':   cmd_chain,
    'log':     cmd_log,
    'history': cmd_history,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print('帝王系统 · Agent 自建调度')
        print()
        print('用法: python3 agent_invoke.py <命令> [参数]')
        print()
        print('命令:')
        print('  invoke   唤起目标 agent 并传递任务')
        print('  chain    查看敕令调度链路')
        print('  log      查看最近调度日志')
        print('  history  查看某 agent 的调度历史')
        print()
        print('示例:')
        print('  # 尚书令唤起将作监执行后端任务')
        print('  python3 agent_invoke.py invoke shangshuling jiangzuo "实现用户认证 JWT 服务" --edict CL-001')
        print()
        print('  # 中书令唤起尚书令派发任务')
        print('  python3 agent_invoke.py invoke zhongshuling shangshuling "审核通过，请派发以下子任务..." --edict CL-001')
        print()
        print('  # 异步唤起（不等待结果）')
        print('  python3 agent_invoke.py invoke shangshuling xingbu "执行安全扫描" --edict CL-001 --async')
        print()
        print('  # 查看敕令调度链路')
        print('  python3 agent_invoke.py chain CL-001')
        sys.exit(1)

    cmd = sys.argv[1]
    COMMANDS[cmd](sys.argv[2:])


if __name__ == '__main__':
    main()
