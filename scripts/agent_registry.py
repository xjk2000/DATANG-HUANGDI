#!/usr/bin/env python3
"""
Agent 注册表 · 帝王系统共享常量

所有脚本统一从此模块导入 Agent 元数据、部门映射、权限矩阵，
消除跨脚本重复定义、防止不一致。

用法：
    from agent_registry import AGENTS, AGENT_NAMES, AGENT_DEPARTMENTS, ...

作者：XuJiaKai
"""

# ── 全部合法 Agent ID（三省六部五监 = 16 个）──────────────────
ALL_AGENT_IDS = [
    # 三省
    'zhongshuling', 'zhongshu_sheren', 'shizhong', 'jishizhong', 'shangshuling',
    # 六部
    'libu', 'hubu', 'libu_protocol', 'bingbu', 'xingbu', 'gongbu',
    # 五监
    'jiangzuo', 'shaofu', 'junqi', 'dushui', 'sinong',
]

VALID_AGENTS = set(ALL_AGENT_IDS)

# ── 核心流转 Agent（日常 6 个）────────────────────────────────
CORE_AGENTS = [
    'zhongshuling', 'shangshuling',
    'jiangzuo', 'shaofu', 'xingbu', 'hubu',
]

CORE_AGENT_SET = set(CORE_AGENTS)

# ── Agent 中文名 ─────────────────────────────────────────────
AGENT_NAMES = {
    'zhongshuling':    '中书令',
    'zhongshu_sheren': '中书舍人',
    'shizhong':        '侍中侍郎',
    'jishizhong':      '给事中',
    'shangshuling':    '尚书令',
    'libu':            '吏部',
    'hubu':            '户部',
    'libu_protocol':   '礼部',
    'bingbu':          '兵部',
    'xingbu':          '刑部',
    'gongbu':          '工部',
    'jiangzuo':        '将作监',
    'shaofu':          '少府监',
    'junqi':           '军器监',
    'dushui':          '都水监',
    'sinong':          '司农监',
}

# ── Agent → 部门（省/部/监）映射 ─────────────────────────────
AGENT_DEPARTMENTS = {
    # 三省
    'zhongshuling':    '中书省',
    'zhongshu_sheren': '中书省',
    'shizhong':        '门下省',
    'jishizhong':      '门下省',
    'shangshuling':    '尚书省',
    # 六部
    'libu':            '吏部',
    'hubu':            '户部',
    'libu_protocol':   '礼部',
    'bingbu':          '兵部',
    'xingbu':          '刑部',
    'gongbu':          '工部',
    # 五监
    'jiangzuo':        '将作监',
    'shaofu':          '少府监',
    'junqi':           '军器监',
    'dushui':          '都水监',
    'sinong':          '司农监',
}

# ── Agent 带职责标签（用于派令模板等展示场景）─────────────────
AGENT_LABELS = {
    'zhongshuling':    '中书令（接旨+审核+回奏）',
    'zhongshu_sheren': '中书舍人（辅助分析）',
    'shizhong':        '侍中侍郎（审查封驳）',
    'jishizhong':      '给事中（逐条排查）',
    'shangshuling':    '尚书令（任务调度+汇总）',
    'libu':            '吏部（Agent 生命周期）',
    'hubu':            '户部（数据+日志+运维）',
    'libu_protocol':   '礼部（API 规范+协议）',
    'bingbu':          '兵部（K8s+CI/CD）',
    'xingbu':          '刑部（测试+审计+安全）',
    'gongbu':          '工部（公共类库+中间件）',
    'jiangzuo':        '将作监（后端开发+基建）',
    'shaofu':          '少府监（前端与交互）',
    'junqi':           '军器监（加解密+安全工具）',
    'dushui':          '都水监（Kafka+Flink）',
    'sinong':          '司农监（爬虫+模型+RAG）',
}

# ── Agent 元数据（供 Manager 和配置同步使用）──────────────────
AGENT_META = {
    'zhongshuling':    {'name': '中书令',   'group': '中书省', 'role': '取旨起草'},
    'zhongshu_sheren': {'name': '中书舍人', 'group': '中书省', 'role': '记录辅析'},
    'shizhong':        {'name': '侍中侍郎', 'group': '门下省', 'role': '审查决策'},
    'jishizhong':      {'name': '给事中',   'group': '门下省', 'role': '排查驳正'},
    'shangshuling':    {'name': '尚书令',   'group': '尚书省', 'role': '派发协调'},
    'libu':            {'name': '吏部',     'group': '六部',   'role': 'Agent 生命周期管理'},
    'hubu':            {'name': '户部',     'group': '六部',   'role': '数据库与报表'},
    'libu_protocol':   {'name': '礼部',     'group': '六部',   'role': 'API 协议规范'},
    'bingbu':          {'name': '兵部',     'group': '六部',   'role': 'CI/CD 与运维'},
    'xingbu':          {'name': '刑部',     'group': '六部',   'role': '测试与审计'},
    'gongbu':          {'name': '工部',     'group': '六部',   'role': '基础设施'},
    'jiangzuo':        {'name': '将作监',   'group': '五监',   'role': '核心业务开发'},
    'shaofu':          {'name': '少府监',   'group': '五监',   'role': '前端与交互'},
    'junqi':           {'name': '军器监',   'group': '五监',   'role': '安全工具'},
    'dushui':          {'name': '都水监',   'group': '五监',   'role': '流计算'},
    'sinong':          {'name': '司农监',   'group': '五监',   'role': '算法与数据'},
}

# ── 调度权限矩阵（谁可以唤起谁）─────────────────────────────
# 核心规则：
#   中书令 → 尚书令
#   尚书令 → 所有执行部门（六部+五监）
#   门下省 → 尚书令、中书令
#   执行部门之间不可互相唤起
INVOKE_PERMISSIONS = {
    'zhongshuling':    {'shangshuling'},
    'zhongshu_sheren': {'zhongshuling'},
    'shizhong':        {'shangshuling', 'zhongshuling'},
    'jishizhong':      {'shizhong'},
    'shangshuling':    {
        'zhongshuling',
        'libu', 'hubu', 'libu_protocol', 'bingbu', 'xingbu', 'gongbu',
        'jiangzuo', 'shaofu', 'junqi', 'dushui', 'sinong',
    },
    # 执行部门只能回报尚书令
    'libu':            {'shangshuling'},
    'hubu':            {'shangshuling'},
    'libu_protocol':   {'shangshuling'},
    'bingbu':          {'shangshuling'},
    'xingbu':          {'shangshuling'},
    'gongbu':          {'shangshuling'},
    'jiangzuo':        {'shangshuling'},
    'shaofu':          {'shangshuling'},
    'junqi':           {'shangshuling'},
    'dushui':          {'shangshuling'},
    'sinong':          {'shangshuling'},
}


def can_invoke(source: str, target: str) -> bool:
    """检查 source 是否有权限唤起 target"""
    allowed = INVOKE_PERMISSIONS.get(source, set())
    return target in allowed


def get_agent_name(agent_id: str) -> str:
    """获取 Agent 中文名，不存在则返回 ID"""
    return AGENT_NAMES.get(agent_id, agent_id)


def get_department(agent_id: str) -> str:
    """获取 Agent 所属部门，不存在则返回 '未知'"""
    return AGENT_DEPARTMENTS.get(agent_id, '未知')
