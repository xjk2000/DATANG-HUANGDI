#!/usr/bin/env python3
"""
帝王系统 · 翰林院看板 API 服务器

零外部依赖，纯 Python 标准库实现。
提供 REST API + 静态文件服务。

端口: 7891
"""

import http.server
import json
import os
import socketserver
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# ─── 路径 ───────────────────────────────────────────────────
REPO_DIR = os.environ.get('REPO_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(REPO_DIR, 'data')
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(REPO_DIR, 'scripts')

TASKS_FILE = os.path.join(DATA_DIR, 'tasks_source.json')
LIVE_STATUS_FILE = os.path.join(DATA_DIR, 'live_status.json')
AGENT_CONFIG_FILE = os.path.join(DATA_DIR, 'agent_config.json')
SUMMARY_FILE = os.path.join(DATA_DIR, 'dashboard_summary.json')
AUDIT_LOG_FILE = os.path.join(DATA_DIR, 'kanban_audit.log')

PORT = int(os.environ.get('PORT', 7891))

# ─── Agent 元数据 ───────────────────────────────────────────
AGENT_META = {
    'zhongshuling':    {'name': '中书令',   'emoji': '📜', 'group': '中书省', 'role': '取旨起草'},
    'zhongshu_sheren': {'name': '中书舍人', 'emoji': '📝', 'group': '中书省', 'role': '记录辅析'},
    'shizhong':        {'name': '侍中侍郎', 'emoji': '🔍', 'group': '门下省', 'role': '审查决策'},
    'jishizhong':      {'name': '给事中',   'emoji': '⚖️', 'group': '门下省', 'role': '排查驳正'},
    'shangshuling':    {'name': '尚书令',   'emoji': '📮', 'group': '尚书省', 'role': '派发协调'},
    'libu':            {'name': '吏部',     'emoji': '👥', 'group': '六部',   'role': 'HR & Lifecycle'},
    'hubu':            {'name': '户部',     'emoji': '💰', 'group': '六部',   'role': 'Data & Biz'},
    'libu_protocol':   {'name': '礼部',     'emoji': '📋', 'group': '六部',   'role': 'API & Standard'},
    'bingbu':          {'name': '兵部',     'emoji': '⚔️', 'group': '六部',   'role': 'SRE & Infra'},
    'xingbu':          {'name': '刑部',     'emoji': '🔒', 'group': '六部',   'role': 'QA & Audit'},
    'gongbu':          {'name': '工部',     'emoji': '🔧', 'group': '六部',   'role': 'Platform & Base'},
    'jiangzuo':        {'name': '将作监',   'emoji': '🏗️', 'group': '五监',   'role': '核心业务开发'},
    'shaofu':          {'name': '少府监',   'emoji': '🎨', 'group': '五监',   'role': '前端与交互'},
    'junqi':           {'name': '军器监',   'emoji': '🛡️', 'group': '五监',   'role': '安全工具'},
    'dushui':          {'name': '都水监',   'emoji': '🌊', 'group': '五监',   'role': '流计算'},
    'sinong':          {'name': '司农监',   'emoji': '🌾', 'group': '五监',   'role': '算法与数据'},
}

# 敕令状态标签
STATE_LABELS = {
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


# ─── 辅助函数 ───────────────────────────────────────────────

def read_json(path, default=None):
    """安全读取 JSON 文件"""
    if default is None:
        default = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def json_response(handler, data, status=200):
    """发送 JSON 响应"""
    body = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(body)))
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    handler.send_header('Access-Control-Allow-Headers', 'Content-Type')
    handler.end_headers()
    try:
        handler.wfile.write(body)
    except BrokenPipeError:
        pass


def error_response(handler, message, status=400):
    json_response(handler, {'error': message}, status)


# ─── 请求处理器 ─────────────────────────────────────────────

class DiWangHandler(http.server.SimpleHTTPRequestHandler):
    """帝王系统 HTTP 请求处理器"""

    def __init__(self, *args, **kwargs):
        # 静态文件根目录指向 dashboard/
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)

    def handle(self):
        """覆盖 handle 以静默处理 BrokenPipeError"""
        try:
            super().handle()
        except BrokenPipeError:
            pass

    def log_message(self, format, *args):
        """自定义日志格式"""
        ts = time.strftime('%H:%M:%S')
        print(f"[{ts}] {args[0]}" if args else f"[{ts}] {format}")

    def do_OPTIONS(self):
        """CORS 预检请求"""
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # API 路由
        if path == '/api/tasks':
            self._api_tasks(query)
        elif path == '/api/task' and 'id' in query:
            self._api_task_detail(query['id'][0])
        elif path == '/api/agents-status':
            self._api_agents_status()
        elif path == '/api/agents-meta':
            self._api_agents_meta()
        elif path == '/api/summary':
            self._api_summary()
        elif path == '/api/audit-log':
            self._api_audit_log(query)
        elif path == '/api/states':
            json_response(self, STATE_LABELS)
        elif path == '/api/health':
            json_response(self, {'status': 'ok', 'time': now_iso()})
        elif path.startswith('/api/'):
            error_response(self, f'未知 API: {path}', 404)
        else:
            # 静态文件服务
            if path == '/' or path == '':
                self.path = '/index.html'
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            error_response(self, '无效的 JSON 请求体')
            return

        if path == '/api/task/state':
            self._api_update_state(data)
        elif path == '/api/task/cancel':
            self._api_cancel_task(data)
        elif path == '/api/task/create':
            self._api_create_task(data)
        elif path == '/api/scheduler-scan':
            self._api_scheduler_scan(data)
        else:
            error_response(self, f'未知 API: {path}', 404)

    # ─── GET APIs ─────────────────────────────────────────

    def _api_tasks(self, query):
        """获取敕令列表"""
        tasks = read_json(TASKS_FILE, [])
        state_filter = query.get('state', [None])[0]
        org_filter = query.get('org', [None])[0]

        if state_filter:
            tasks = [t for t in tasks if t.get('state') == state_filter]
        if org_filter:
            tasks = [t for t in tasks if t.get('org') == org_filter]

        # 添加状态标签
        for t in tasks:
            t['stateLabel'] = STATE_LABELS.get(t.get('state', ''), t.get('state', ''))
            # 心跳检测
            updated = t.get('updated_at', '')
            if updated and t.get('state') in ('Executing', 'Dispatching', 'MenxiaReview', 'ZhongshuDraft'):
                try:
                    updated_dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                    now_dt = datetime.now(timezone.utc)
                    delta_min = (now_dt - updated_dt).total_seconds() / 60
                    if delta_min < 5:
                        t['heartbeat'] = 'active'
                    elif delta_min < 30:
                        t['heartbeat'] = 'idle'
                    else:
                        t['heartbeat'] = 'stale'
                except Exception:
                    t['heartbeat'] = 'unknown'
            else:
                t['heartbeat'] = 'none'

        json_response(self, tasks)

    def _api_task_detail(self, task_id):
        """获取单个敕令详情"""
        tasks = read_json(TASKS_FILE, [])
        for t in tasks:
            if t.get('id') == task_id:
                t['stateLabel'] = STATE_LABELS.get(t.get('state', ''), t.get('state', ''))
                json_response(self, t)
                return
        error_response(self, f'敕令不存在: {task_id}', 404)

    def _api_agents_status(self):
        """获取 Agent 实时状态"""
        status = read_json(LIVE_STATUS_FILE, {})
        # 合并元数据
        for agent_id, meta in AGENT_META.items():
            if agent_id in status:
                status[agent_id].update(meta)
            else:
                status[agent_id] = {
                    'id': agent_id,
                    'status': 'unknown',
                    'sessions': 0,
                    **meta,
                }
        json_response(self, status)

    def _api_agents_meta(self):
        """获取 Agent 元数据"""
        json_response(self, AGENT_META)

    def _api_summary(self):
        """获取看板摘要"""
        summary = read_json(SUMMARY_FILE, {})
        if not summary:
            # 实时计算
            tasks = read_json(TASKS_FILE, [])
            from collections import Counter
            state_counts = Counter(t.get('state', 'unknown') for t in tasks)
            org_counts = Counter(t.get('org', '未知') for t in tasks)
            summary = {
                'total': len(tasks),
                'stateCounts': dict(state_counts),
                'orgCounts': dict(org_counts),
                'updatedAt': now_iso(),
            }
        json_response(self, summary)

    def _api_audit_log(self, query):
        """获取审计日志"""
        lines_limit = int(query.get('limit', ['100'])[0])
        try:
            with open(AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            lines = lines[-lines_limit:]
            json_response(self, {'lines': [l.strip() for l in lines]})
        except FileNotFoundError:
            json_response(self, {'lines': []})

    # ─── POST APIs ────────────────────────────────────────

    def _api_update_state(self, data):
        """通过 API 更新敕令状态"""
        task_id = data.get('id', '')
        new_state = data.get('state', '')
        remark = data.get('remark', '')

        if not task_id or not new_state:
            error_response(self, '缺少必要参数: id, state')
            return

        try:
            result = subprocess.run(
                [sys.executable, os.path.join(SCRIPTS_DIR, 'kanban_update.py'),
                 'state', task_id, new_state, remark],
                capture_output=True, text=True, timeout=10,
                env={**os.environ, 'REPO_DIR': REPO_DIR},
            )
            if result.returncode == 0:
                json_response(self, {'ok': True, 'message': result.stdout.strip()})
            else:
                error_response(self, result.stderr.strip() or '状态更新失败')
        except Exception as e:
            error_response(self, f'执行失败: {e}', 500)

    def _api_cancel_task(self, data):
        """通过 API 取消敕令"""
        task_id = data.get('id', '')
        reason = data.get('reason', '看板手动取消')

        if not task_id:
            error_response(self, '缺少必要参数: id')
            return

        try:
            result = subprocess.run(
                [sys.executable, os.path.join(SCRIPTS_DIR, 'kanban_update.py'),
                 'cancel', task_id, reason],
                capture_output=True, text=True, timeout=10,
                env={**os.environ, 'REPO_DIR': REPO_DIR},
            )
            if result.returncode == 0:
                json_response(self, {'ok': True, 'message': result.stdout.strip()})
            else:
                error_response(self, result.stderr.strip() or '取消失败')
        except Exception as e:
            error_response(self, f'执行失败: {e}', 500)

    def _api_create_task(self, data):
        """通过 API 创建敕令"""
        task_id = data.get('id', '')
        title = data.get('title', '')
        state = data.get('state', 'Imperial')
        org = data.get('org', '中书省')
        official = data.get('official', '中书令')

        if not task_id or not title:
            error_response(self, '缺少必要参数: id, title')
            return

        try:
            result = subprocess.run(
                [sys.executable, os.path.join(SCRIPTS_DIR, 'kanban_update.py'),
                 'create', task_id, title, state, org, official],
                capture_output=True, text=True, timeout=10,
                env={**os.environ, 'REPO_DIR': REPO_DIR},
            )
            if result.returncode == 0:
                json_response(self, {'ok': True, 'message': result.stdout.strip()})
            else:
                error_response(self, result.stderr.strip() or '创建失败')
        except Exception as e:
            error_response(self, f'执行失败: {e}', 500)

    def _api_scheduler_scan(self, data):
        """手动触发巡检扫描"""
        threshold_sec = data.get('thresholdSec', 1800)
        tasks = read_json(TASKS_FILE, [])
        now_dt = datetime.now(timezone.utc)
        stale = []

        for t in tasks:
            if t.get('state') in ('Executing', 'Dispatching', 'MenxiaReview'):
                updated = t.get('updated_at', '')
                if updated:
                    try:
                        updated_dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                        delta = (now_dt - updated_dt).total_seconds()
                        if delta > threshold_sec:
                            stale.append({
                                'id': t['id'],
                                'state': t['state'],
                                'staleSec': round(delta),
                            })
                    except Exception:
                        pass

        json_response(self, {
            'scanned': len(tasks),
            'staleCount': len(stale),
            'staleTasks': stale,
            'thresholdSec': threshold_sec,
        })


# ─── 启动服务器 ─────────────────────────────────────────────

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # 初始化空数据文件
    for f, default in [
        (TASKS_FILE, '[]'),
        (LIVE_STATUS_FILE, '{}'),
        (AGENT_CONFIG_FILE, '{}'),
        (SUMMARY_FILE, '{}'),
    ]:
        if not os.path.exists(f):
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write(default)

    print()
    print('\033[0;34m╔════════════════════════════════════════╗\033[0m')
    print('\033[0;34m║  ⚔️  帝王系统 · 翰林院看板服务器       ║\033[0m')
    print('\033[0;34m╚════════════════════════════════════════╝\033[0m')
    print()
    print(f'  📡 API 服务:  http://127.0.0.1:{PORT}/api/')
    print(f'  📋 看板界面:  http://127.0.0.1:{PORT}/')
    print(f'  📂 数据目录:  {DATA_DIR}')
    print()

    with ReusableTCPServer(('', PORT), DiWangHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n\033[0;33m⚠️  服务已停止\033[0m')


if __name__ == '__main__':
    main()
