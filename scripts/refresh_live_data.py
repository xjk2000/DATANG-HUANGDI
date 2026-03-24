#!/usr/bin/env python3
"""
刷新看板实时数据。

统计各状态任务数量、部门分布，生成看板摘要数据。
"""

import json
import os
from datetime import datetime, timezone
from collections import Counter

REPO_DIR = os.environ.get('REPO_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(REPO_DIR, 'data')
TASKS_FILE = os.path.join(DATA_DIR, 'tasks_source.json')


def now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def refresh():
    if not os.path.exists(TASKS_FILE):
        return

    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    # 状态统计
    state_counts = Counter(t.get('state', 'unknown') for t in tasks)

    # 部门统计
    org_counts = Counter(t.get('org', '未知') for t in tasks)

    # 心跳检测：超过 30 分钟未更新的执行中任务标记为停滞
    now = datetime.now(timezone.utc)
    stale_tasks = []
    for t in tasks:
        if t.get('state') in ('Executing', 'Dispatching', 'MenxiaReview', 'ZhongshuDraft'):
            updated = t.get('updated_at', '')
            if updated:
                try:
                    updated_dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                    delta_min = (now - updated_dt).total_seconds() / 60
                    if delta_min > 30:
                        stale_tasks.append({
                            'id': t['id'],
                            'title': t.get('title', ''),
                            'state': t.get('state', ''),
                            'stale_minutes': round(delta_min),
                        })
                except Exception:
                    pass

    summary = {
        'total': len(tasks),
        'stateCounts': dict(state_counts),
        'orgCounts': dict(org_counts),
        'staleTasks': stale_tasks,
        'updatedAt': now_iso(),
    }

    output_path = os.path.join(DATA_DIR, 'dashboard_summary.json')
    tmp_path = output_path + f'.tmp-{os.getpid()}'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, output_path)

    active = state_counts.get('Executing', 0) + state_counts.get('Dispatching', 0)
    done = state_counts.get('Done', 0)
    print(f"[refresh] 摘要已更新: {len(tasks)} 敕令, {active} 执行中, {done} 已完成, {len(stale_tasks)} 停滞")


if __name__ == '__main__':
    refresh()
