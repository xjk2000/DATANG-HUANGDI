#!/usr/bin/env python3
"""
Agent 配置同步脚本。

从 openclaw.json 读取 Agent 配置信息，
与帝王系统的 Agent 元数据合并，输出到 data/agent_config.json。
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent_registry import ALL_AGENT_IDS, AGENT_META

REPO_DIR = os.environ.get('REPO_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(REPO_DIR, 'data')
# 支持通过环境变量配置 OpenClaw 路径，默认为 ~/.openclaw
OC_HOME = os.environ.get('OPENCLAW_HOME', os.path.join(str(Path.home()), '.openclaw'))
OC_CFG = os.path.join(OC_HOME, 'openclaw.json')

ALL_AGENTS = ALL_AGENT_IDS


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # 读取 openclaw.json
    oc_agents = {}
    if os.path.exists(OC_CFG):
        try:
            with open(OC_CFG, 'r', encoding='utf-8') as f:
                oc_cfg = json.load(f)
            for agent in oc_cfg.get('agents', {}).get('list', []):
                oc_agents[agent.get('id', '')] = agent
        except Exception as e:
            print(f"[sync_agent_config] 读取 openclaw.json 失败: {e}")

    # 合并配置
    config = {}
    for agent_id in ALL_AGENTS:
        meta = AGENT_META.get(agent_id, {})
        oc = oc_agents.get(agent_id, {})

        model = oc.get('model', {})
        if isinstance(model, str):
            model_name = model
        elif isinstance(model, dict):
            model_name = model.get('primary', '默认')
        else:
            model_name = '默认'

        config[agent_id] = {
            'id': agent_id,
            'name': meta.get('name', agent_id),
            'group': meta.get('group', '未知'),
            'role': meta.get('role', ''),
            'workspace': oc.get('workspace', f'{OC_HOME}/workspace-{agent_id}'),
            'model': model_name,
            'subagents': oc.get('subagents', {}),
            'registered': agent_id in oc_agents,
        }

    # 写入
    output_path = os.path.join(DATA_DIR, 'agent_config.json')
    tmp_path = output_path + f'.tmp-{os.getpid()}'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, output_path)

    registered = sum(1 for v in config.values() if v['registered'])
    print(f"[sync_agent_config] 完成: {len(config)} agents, {registered} 已注册")


if __name__ == '__main__':
    main()
