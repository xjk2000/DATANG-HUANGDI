#!/usr/bin/env python3
"""
帝王系统 · 看板状态机端到端测试

测试核心流程：创建敕令 → 状态流转 → 门下封驳 → 重新提交 → 准奏 → 派发 → 执行 → 完成
"""

import json
import os
import subprocess
import sys
import tempfile
import shutil
import unittest

# 测试用临时目录
TEST_DIR = None
SCRIPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'scripts', 'kanban_update.py'
)


def run_kanban(*args, expect_fail=False):
    """运行 kanban_update.py 命令"""
    env = {**os.environ, 'REPO_DIR': TEST_DIR}
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH] + list(args),
        capture_output=True, text=True, env=env,
    )
    if not expect_fail and result.returncode != 0:
        raise AssertionError(
            f"命令失败 (rc={result.returncode}): {' '.join(args)}\n"
            f"stderr: {result.stderr}\nstdout: {result.stdout}"
        )
    if expect_fail and result.returncode == 0:
        raise AssertionError(
            f"命令应该失败但成功了: {' '.join(args)}\nstdout: {result.stdout}"
        )
    return result


def read_tasks():
    """读取任务数据"""
    tasks_file = os.path.join(TEST_DIR, 'data', 'tasks_source.json')
    with open(tasks_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_task(task_id):
    """查找指定任务"""
    for t in read_tasks():
        if t['id'] == task_id:
            return t
    return None


class TestKanbanStateMachine(unittest.TestCase):
    """测试看板状态机"""

    @classmethod
    def setUpClass(cls):
        global TEST_DIR
        TEST_DIR = tempfile.mkdtemp(prefix='diwang-test-')
        os.makedirs(os.path.join(TEST_DIR, 'data'), exist_ok=True)
        # 初始化空任务文件
        with open(os.path.join(TEST_DIR, 'data', 'tasks_source.json'), 'w') as f:
            json.dump([], f)

    @classmethod
    def tearDownClass(cls):
        if TEST_DIR and os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)

    def test_01_create_task(self):
        """测试创建敕令"""
        run_kanban('create', 'CL-TEST-001', '测试敕令一号', 'Imperial', '中书省', '中书令')
        task = find_task('CL-TEST-001')
        self.assertIsNotNone(task)
        self.assertEqual(task['state'], 'Imperial')
        self.assertEqual(task['title'], '测试敕令一号')
        self.assertEqual(task['org'], '中书省')
        self.assertEqual(task['official'], '中书令')
        self.assertTrue(len(task['flow_log']) >= 1)

    def test_02_duplicate_create_rejected(self):
        """测试重复创建被拒绝"""
        result = run_kanban('create', 'CL-TEST-001', '重复', 'Imperial', '中书省', '中书令', expect_fail=True)
        self.assertIn('已存在', result.stderr)

    def test_03_state_imperial_to_zhongshu(self):
        """测试状态：皇帝下旨 → 中书起草"""
        run_kanban('state', 'CL-TEST-001', 'ZhongshuDraft', '中书令已接旨，开始起草')
        task = find_task('CL-TEST-001')
        self.assertEqual(task['state'], 'ZhongshuDraft')

    def test_04_state_zhongshu_to_menxia(self):
        """测试状态：中书起草 → 门下审议"""
        run_kanban('state', 'CL-TEST-001', 'MenxiaReview', '敕令提交门下省审议')
        task = find_task('CL-TEST-001')
        self.assertEqual(task['state'], 'MenxiaReview')

    def test_05_state_menxia_reject(self):
        """测试状态：门下审议 → 封驳退回中书"""
        run_kanban('state', 'CL-TEST-001', 'ZhongshuDraft', '门下封驳，退回中书省修改')
        task = find_task('CL-TEST-001')
        self.assertEqual(task['state'], 'ZhongshuDraft')

    def test_06_resubmit_to_menxia(self):
        """测试重新提交门下"""
        run_kanban('state', 'CL-TEST-001', 'MenxiaReview', '修改后重新提交审议')
        task = find_task('CL-TEST-001')
        self.assertEqual(task['state'], 'MenxiaReview')

    def test_07_menxia_approve(self):
        """测试门下准奏"""
        run_kanban('state', 'CL-TEST-001', 'Approved', '门下准奏')
        task = find_task('CL-TEST-001')
        self.assertEqual(task['state'], 'Approved')

    def test_08_dispatch(self):
        """测试尚书派发"""
        run_kanban('state', 'CL-TEST-001', 'Dispatching', '尚书令接令，分析派发')
        task = find_task('CL-TEST-001')
        self.assertEqual(task['state'], 'Dispatching')

    def test_09_executing(self):
        """测试进入执行"""
        run_kanban('state', 'CL-TEST-001', 'Executing', '将作监开始开发')
        task = find_task('CL-TEST-001')
        self.assertEqual(task['state'], 'Executing')

    def test_10_done(self):
        """测试完成"""
        run_kanban('done', 'CL-TEST-001', '业务服务已完成开发', '一句话总结：开发完成')
        task = find_task('CL-TEST-001')
        self.assertEqual(task['state'], 'Done')

    def test_11_done_cannot_change(self):
        """测试已完成不可再修改"""
        result = run_kanban('state', 'CL-TEST-001', 'Executing', '想再改', expect_fail=True)
        self.assertIn('已完成', result.stderr)

    def test_12_flow_log(self):
        """测试流转记录"""
        run_kanban('create', 'CL-TEST-002', '流转测试', 'Imperial', '中书省', '中书令')
        run_kanban('flow', 'CL-TEST-002', '皇上', '中书令', '下旨测试')
        run_kanban('flow', 'CL-TEST-002', '中书令', '侍中侍郎', '提交审议')
        task = find_task('CL-TEST-002')
        # 创建时有 1 条 flow，加上 2 条手动 flow = 3 条
        self.assertEqual(len(task['flow_log']), 3)
        self.assertEqual(task['flow_log'][-1]['from'], '中书令')
        self.assertEqual(task['flow_log'][-1]['to'], '侍中侍郎')

    def test_13_progress(self):
        """测试进度上报"""
        run_kanban('progress', 'CL-TEST-002', '正在分析旨意', '分析🔄|起草|审议')
        task = find_task('CL-TEST-002')
        self.assertEqual(task['progress'], '正在分析旨意')
        self.assertEqual(task['plan'], '分析🔄|起草|审议')

    def test_14_todo(self):
        """测试子任务上报"""
        run_kanban('todo', 'CL-TEST-002', '1', '需求分析', 'completed', '--detail', '完成了需求分析')
        run_kanban('todo', 'CL-TEST-002', '2', '方案设计', 'doing')
        task = find_task('CL-TEST-002')
        self.assertEqual(len(task['todos']), 2)
        self.assertEqual(task['todos'][0]['status'], 'completed')
        self.assertEqual(task['todos'][1]['status'], 'doing')

    def test_15_cancel(self):
        """测试取消"""
        run_kanban('create', 'CL-TEST-003', '即将取消的敕令', 'Imperial', '中书省', '中书令')
        run_kanban('cancel', 'CL-TEST-003', '皇帝改主意了')
        task = find_task('CL-TEST-003')
        self.assertEqual(task['state'], 'Cancelled')

    def test_16_illegal_transition_rejected(self):
        """测试非法状态转换被拒绝"""
        run_kanban('create', 'CL-TEST-004', '非法跳转测试', 'Imperial', '中书省', '中书令')
        # Imperial 不能直接跳到 Executing
        result = run_kanban('state', 'CL-TEST-004', 'Executing', '试图跳过', expect_fail=True)
        self.assertIn('非法状态转换', result.stderr)

    def test_17_title_cleaning(self):
        """测试标题清洗"""
        run_kanban('create', 'CL-TEST-005',
                   '这是一个 /path/to/file.txt 包含路径的 https://example.com 标题',
                   'Imperial', '中书省', '中书令')
        task = find_task('CL-TEST-005')
        # 路径和 URL 应该被清洗掉
        self.assertNotIn('/path/to/file.txt', task['title'])
        self.assertNotIn('https://example.com', task['title'])

    def test_18_list(self):
        """测试列出敕令"""
        result = run_kanban('list')
        self.assertIn('CL-TEST-001', result.stdout)

    def test_19_list_with_filter(self):
        """测试筛选列出"""
        result = run_kanban('list', '--state', 'Done')
        self.assertIn('CL-TEST-001', result.stdout)

    def test_20_blocked_state(self):
        """测试阻塞状态"""
        run_kanban('create', 'CL-TEST-006', '阻塞测试', 'Imperial', '尚书省', '尚书令')
        run_kanban('state', 'CL-TEST-006', 'ZhongshuDraft', '中书起草')
        run_kanban('state', 'CL-TEST-006', 'MenxiaReview', '提交审议')
        run_kanban('state', 'CL-TEST-006', 'Approved', '准奏')
        run_kanban('state', 'CL-TEST-006', 'Dispatching', '派发')
        run_kanban('state', 'CL-TEST-006', 'Executing', '执行中')
        run_kanban('state', 'CL-TEST-006', 'Blocked', '等待外部依赖')
        task = find_task('CL-TEST-006')
        self.assertEqual(task['state'], 'Blocked')
        # 从 Blocked 可以回到 Executing
        run_kanban('state', 'CL-TEST-006', 'Executing', '依赖已解决，恢复执行')
        task = find_task('CL-TEST-006')
        self.assertEqual(task['state'], 'Executing')


class TestKanbanEdgeCases(unittest.TestCase):
    """测试边界情况"""

    @classmethod
    def setUpClass(cls):
        global TEST_DIR
        if TEST_DIR is None:
            TEST_DIR = tempfile.mkdtemp(prefix='diwang-test-')
            os.makedirs(os.path.join(TEST_DIR, 'data'), exist_ok=True)
            with open(os.path.join(TEST_DIR, 'data', 'tasks_source.json'), 'w') as f:
                json.dump([], f)

    def test_nonexistent_task(self):
        """测试操作不存在的任务"""
        result = run_kanban('state', 'NONEXISTENT', 'Done', '不存在', expect_fail=True)
        self.assertIn('不存在', result.stderr)

    def test_unknown_state(self):
        """测试未知状态"""
        run_kanban('create', 'CL-EDGE-001', '边界测试', 'Imperial', '中书省', '中书令')
        result = run_kanban('state', 'CL-EDGE-001', 'FakeState', '假状态', expect_fail=True)
        self.assertIn('未知状态', result.stderr)

    def test_todo_invalid_status(self):
        """测试子任务无效状态"""
        run_kanban('create', 'CL-EDGE-002', '子任务状态测试', 'Imperial', '中书省', '中书令')
        result = run_kanban('todo', 'CL-EDGE-002', '1', '测试', 'invalid_status', expect_fail=True)
        self.assertIn('未知子任务状态', result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
