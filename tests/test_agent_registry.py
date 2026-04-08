#!/usr/bin/env python3
"""
帝王系统 · Agent 注册表与调度权限测试

测试 agent_registry.py 的常量完整性、权限矩阵正确性，
以及 agent_invoke.py 的权限校验行为。
"""

import os
import subprocess
import sys
import unittest

# 导入被测模块
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'scripts',
))
from agent_registry import (
    ALL_AGENT_IDS, VALID_AGENTS, CORE_AGENTS, CORE_AGENT_SET,
    AGENT_NAMES, AGENT_DEPARTMENTS, AGENT_LABELS, AGENT_META,
    INVOKE_PERMISSIONS, can_invoke, get_agent_name, get_department,
)

INVOKE_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'scripts', 'agent_invoke.py',
)


class TestAgentRegistryIntegrity(unittest.TestCase):
    """测试注册表数据完整性"""

    def test_all_agent_ids_count(self):
        """16 个 Agent"""
        self.assertEqual(len(ALL_AGENT_IDS), 16)

    def test_valid_agents_matches_all(self):
        """VALID_AGENTS 与 ALL_AGENT_IDS 一致"""
        self.assertEqual(VALID_AGENTS, set(ALL_AGENT_IDS))

    def test_core_agents_subset(self):
        """核心 6 Agent 是全集的子集"""
        self.assertEqual(len(CORE_AGENTS), 6)
        self.assertTrue(CORE_AGENT_SET.issubset(VALID_AGENTS))

    def test_every_agent_has_name(self):
        """每个 Agent 都有中文名"""
        for aid in ALL_AGENT_IDS:
            self.assertIn(aid, AGENT_NAMES, f'{aid} 缺少中文名')

    def test_every_agent_has_department(self):
        """每个 Agent 都有部门映射"""
        for aid in ALL_AGENT_IDS:
            self.assertIn(aid, AGENT_DEPARTMENTS, f'{aid} 缺少部门映射')

    def test_every_agent_has_label(self):
        """每个 Agent 都有职责标签"""
        for aid in ALL_AGENT_IDS:
            self.assertIn(aid, AGENT_LABELS, f'{aid} 缺少职责标签')

    def test_every_agent_has_meta(self):
        """每个 Agent 都有元数据"""
        for aid in ALL_AGENT_IDS:
            self.assertIn(aid, AGENT_META, f'{aid} 缺少元数据')
            meta = AGENT_META[aid]
            self.assertIn('name', meta)
            self.assertIn('group', meta)
            self.assertIn('role', meta)

    def test_no_extra_agents_in_maps(self):
        """映射表不包含未注册的 Agent"""
        for mapping_name, mapping in [
            ('AGENT_NAMES', AGENT_NAMES),
            ('AGENT_DEPARTMENTS', AGENT_DEPARTMENTS),
            ('AGENT_LABELS', AGENT_LABELS),
            ('AGENT_META', AGENT_META),
        ]:
            extra = set(mapping.keys()) - VALID_AGENTS
            self.assertEqual(extra, set(), f'{mapping_name} 包含未注册 Agent: {extra}')


class TestInvokePermissions(unittest.TestCase):
    """测试调度权限矩阵"""

    def test_every_agent_has_permissions(self):
        """每个 Agent 都配置了调度权限"""
        for aid in ALL_AGENT_IDS:
            self.assertIn(aid, INVOKE_PERMISSIONS, f'{aid} 缺少调度权限配置')

    def test_permission_targets_are_valid(self):
        """权限矩阵中的目标 Agent 都是合法的"""
        for source, targets in INVOKE_PERMISSIONS.items():
            self.assertIn(source, VALID_AGENTS, f'权限矩阵包含非法来源: {source}')
            for target in targets:
                self.assertIn(target, VALID_AGENTS,
                              f'{source} 的目标 {target} 不是合法 Agent')

    def test_zhongshuling_can_invoke_shangshuling(self):
        """中书令可唤起尚书令"""
        self.assertTrue(can_invoke('zhongshuling', 'shangshuling'))

    def test_zhongshuling_cannot_invoke_jiangzuo(self):
        """中书令不可直接唤起将作监"""
        self.assertFalse(can_invoke('zhongshuling', 'jiangzuo'))

    def test_shangshuling_can_invoke_all_exec(self):
        """尚书令可唤起所有执行部门"""
        exec_agents = [
            'libu', 'hubu', 'libu_protocol', 'bingbu', 'xingbu', 'gongbu',
            'jiangzuo', 'shaofu', 'junqi', 'dushui', 'sinong',
        ]
        for aid in exec_agents:
            self.assertTrue(can_invoke('shangshuling', aid),
                            f'尚书令应该能唤起 {aid}')

    def test_exec_agents_cannot_cross_invoke(self):
        """执行部门之间不可互相唤起"""
        exec_agents = ['jiangzuo', 'shaofu', 'xingbu', 'hubu']
        for src in exec_agents:
            for tgt in exec_agents:
                if src != tgt:
                    self.assertFalse(can_invoke(src, tgt),
                                     f'{src} 不应该能唤起 {tgt}')

    def test_exec_agents_can_invoke_shangshuling(self):
        """执行部门只能回报尚书令"""
        exec_agents = [
            'libu', 'hubu', 'libu_protocol', 'bingbu', 'xingbu', 'gongbu',
            'jiangzuo', 'shaofu', 'junqi', 'dushui', 'sinong',
        ]
        for aid in exec_agents:
            self.assertTrue(can_invoke(aid, 'shangshuling'),
                            f'{aid} 应该能唤起尚书令')
            # 不能唤起中书令
            self.assertFalse(can_invoke(aid, 'zhongshuling'),
                             f'{aid} 不应该能唤起中书令')

    def test_no_self_invoke(self):
        """Agent 不可自我唤起"""
        for aid in ALL_AGENT_IDS:
            self.assertFalse(can_invoke(aid, aid),
                             f'{aid} 不应该能自我唤起')


class TestHelperFunctions(unittest.TestCase):
    """测试辅助函数"""

    def test_get_agent_name_known(self):
        self.assertEqual(get_agent_name('zhongshuling'), '中书令')

    def test_get_agent_name_unknown(self):
        self.assertEqual(get_agent_name('nonexistent'), 'nonexistent')

    def test_get_department_known(self):
        self.assertEqual(get_department('jiangzuo'), '将作监')

    def test_get_department_unknown(self):
        self.assertEqual(get_department('nonexistent'), '未知')


class TestAgentInvokeCLI(unittest.TestCase):
    """测试 agent_invoke.py 的 CLI 权限校验"""

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, INVOKE_SCRIPT] + list(args),
            capture_output=True, text=True,
        )

    def test_invalid_source_agent(self):
        """无效来源 Agent 被拒绝"""
        r = self._run('invoke', 'fake_agent', 'shangshuling', '测试')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('无效的来源 Agent', r.stdout)

    def test_invalid_target_agent(self):
        """无效目标 Agent 被拒绝"""
        r = self._run('invoke', 'zhongshuling', 'fake_target', '测试')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('无效的目标 Agent', r.stdout)

    def test_permission_denied(self):
        """权限拒绝"""
        r = self._run('invoke', 'jiangzuo', 'xingbu', '跨部门调用')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('权限拒绝', r.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
