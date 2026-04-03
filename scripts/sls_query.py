#!/usr/bin/env python3
"""SLS 日志查询工具（户部专用）

两种使用模式：

  【模式一】查询 SLS 日志（原有接口，完全兼容）：
    python3 sls_query.py <env> <start> <end> <query> [--out <path>]

    env:   production/prod（生产）或 staging/test（测试）
    start/end: "yyyy-MM-dd HH:mm:ss"
    query: SLS 查询语句；service_filter 自动强制追加
    --out: 可选，把完整原始输出保存到文件（避免刷屏）

  【模式二】代码日志模式分析（为户部提供精确关键词）：
    python3 sls_query.py analyze-logs <feature> [--project-dir <path>]

    从 project_dir 的源码中提取含 <feature> 的日志打印语句，
    输出实际日志字符串 → 直接用于模式一的 query 参数。

配置文件 data/diwang.json（安装时已创建，参考 diwang.json.example）：
  {
    "project_dir": "/path/to/your/project",
    "sls": {
      "get_logs_script": "~/projects/get_logs.py",  // 底层脚本路径（默认值）
      "service_filter":  "service:shulex-intelli",  // 强制追加的过滤器
      "environments": { ... }                        // 可选：覆盖默认环境配置
    }
  }
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime

# ─── 默认环境配置 ──────────────────────────────────────────────
_DEFAULT_ENVS = {
    "production": {
        "project":     "shulex-prod-applications-0714",
        "logstore":    "shulex-prod-applications-logstore-0714",
        "description": "生产环境",
    },
    "staging": {
        "project":     "shulex-staging-applications-0714",
        "logstore":    "shulex-staging-applications-logstore-0714",
        "description": "测试环境",
    },
}
_DEFAULT_ENVS["prod"] = _DEFAULT_ENVS["production"]
_DEFAULT_ENVS["test"] = _DEFAULT_ENVS["staging"]

_DEFAULT_SERVICE_FILTER  = "service:shulex-intelli"
_DEFAULT_GET_LOGS_SCRIPT = "~/projects/get_logs.py"
_MAX_PRINT_CHARS         = 12000

# Java/Python/Go 日志调用正则
_LOG_CALL_RE = re.compile(
    r'(log(ger|ging)?|LOG(?:GER)?|LOGGER?)\s*\.\s*'
    r'(info|warn(?:ing)?|error|debug|trace|fatal)\s*\(',
    re.IGNORECASE,
)
_STRING_RE = re.compile(r'"([^"\\]{4,120})"')


# ─── 配置读取 ─────────────────────────────────────────────────
def _read_diwang_json():
    """读取 data/diwang.json 或 ~/.diwang.json，失败时返回 {}"""
    candidates = [
        os.path.join(os.environ.get('REPO_DIR', ''), 'data', 'diwang.json'),
        os.path.expanduser('~/.diwang.json'),
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f'⚠️  读取配置文件失败 {path}: {e}', file=sys.stderr)
    return {}


def _load_sls_settings():
    """加载 SLS 运行时设置（环境表、service filter、底层脚本路径）"""
    raw = _read_diwang_json()
    sls = raw.get('sls', {})

    envs = dict(_DEFAULT_ENVS)
    if isinstance(sls.get('environments'), dict):
        for k, v in sls['environments'].items():
            envs[k.lower()] = v

    service_filter  = sls.get('service_filter',  _DEFAULT_SERVICE_FILTER)
    get_logs_script = os.path.expanduser(
        sls.get('get_logs_script', _DEFAULT_GET_LOGS_SCRIPT)
    )
    project_dir = os.environ.get('PROJECT_DIR', raw.get('project_dir', ''))

    return envs, service_filter, get_logs_script, project_dir


# ─── 工具函数 ─────────────────────────────────────────────────
def _validate_time(t):
    try:
        datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
        return True
    except ValueError:
        return False


def _truncate(text, limit):
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... (输出已截断，共 {len(text)} 字符)\n"


def _force_service_filter(raw_query, service_filter):
    """将 service_filter 强制追加到查询语句末尾。

    无论用户是否写了 service:xxx，最终都包一层
    (raw_query) and <service_filter>
    确保只命中目标服务。
    """
    q = (raw_query or "").strip() or "*"
    overwritten = "service:" in q.lower()
    return f"({q}) and {service_filter}", overwritten


def _print_usage(envs, service_filter):
    print("SLS 日志查询工具（户部专用）")
    print("=" * 60)
    print("用法（模式一）:")
    print("  python3 sls_query.py <环境> <开始时间> <结束时间> <查询语句> [--out <文件>]")
    print()
    print("  环境:", ", ".join(sorted(set(envs.keys()))))
    print("  时间: yyyy-MM-dd HH:mm:ss")
    print(f"  查询: SLS 查询语法（最终强制限定为 {service_filter}）")
    print()
    print("用法（模式二）:")
    print("  python3 sls_query.py analyze-logs <功能关键词> [--project-dir <路径>]")
    print()
    print("示例:")
    print('  python3 sls_query.py analyze-logs UserLogin')
    print('  python3 sls_query.py production "2025-01-01 00:00:00" "2025-01-01 01:00:00" "UserLogin"')
    print('  python3 sls_query.py prod "2025-01-01 00:00:00" "2025-01-01 01:00:00" "level:ERROR" --out /tmp/err.log')
    print()


# ─── 模式二：analyze-logs ──────────────────────────────────────
def cmd_analyze_logs(feature, project_dir):
    """从项目源码提取日志打印语句，输出可直接用于 SLS 查询的关键词"""
    if not project_dir:
        print('❌ 未配置 project_dir，请在 data/diwang.json 中配置，或使用 --project-dir 指定',
              file=sys.stderr)
        sys.exit(2)
    if not os.path.isdir(project_dir):
        print(f'❌ project_dir 路径不存在: {project_dir}', file=sys.stderr)
        sys.exit(2)

    print(f'🔍 代码日志分析: [{feature}]')
    print(f'   项目路径: {project_dir}')
    print('─' * 64)

    def _search(pattern, ext=None):
        """用 rg 搜索，不存在则降级到 grep"""
        cmd = ['rg', '--no-heading', '-n', pattern, project_dir]
        if ext:
            cmd += ['--type', ext]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            return [l.strip() for l in r.stdout.splitlines() if l.strip()]
        except FileNotFoundError:
            inc = f'--include=*.{ext}' if ext else ''
            grep = ['grep', '-rn'] + ([inc] if inc else []) + [pattern, project_dir]
            try:
                r = subprocess.run(grep, capture_output=True, text=True, timeout=20)
                return [l.strip() for l in r.stdout.splitlines() if l.strip()]
            except Exception:
                return []
        except subprocess.TimeoutExpired:
            return []

    # 逐语言收集包含 feature 的日志语句
    hits = []
    for ext in ('java', 'py', 'ts', 'js', 'go'):
        for line in _search(feature, ext):
            if _LOG_CALL_RE.search(line):
                hits.append((ext, line))

    if not hits:
        print(f'⚠️  未在日志语句中直接匹配 [{feature}]，尝试全文搜索...')
        for line in _search(feature)[:15]:
            if _LOG_CALL_RE.search(line):
                hits.append(('?', line))

    if not hits:
        print(f'⚠️  未找到包含 [{feature}] 的日志语句')
        print(f'   建议直接使用 feature 关键词查询 SLS：')
        print(f'   python3 sls_query.py <env> <start> <end> "{feature}"')
        return

    print(f'\n� 找到 {len(hits)} 条日志语句:\n')
    log_strings = []
    for i, (ext, line) in enumerate(hits[:20], 1):
        parts = line.split(':', 2)
        loc  = f'{parts[0]}:{parts[1]}' if len(parts) >= 3 else line[:60]
        code = parts[2].strip() if len(parts) >= 3 else line

        print(f'  [{i}] [{ext}] {loc}')
        print(f'       {code[:120]}')

        for m in _STRING_RE.finditer(code):
            s = m.group(1)
            if len(s) > 5:
                log_strings.append(s)
                print(f'       → 日志内容: "{s}"')
                break
        print()

    unique = list(dict.fromkeys(s for s in log_strings if len(s) > 5))[:6]

    print('─' * 64)
    if unique:
        print('� 推荐 SLS 查询关键词（直接传给模式一的 <查询语句>）:')
        for s in unique:
            print(f'   "{s}"')
        combined = ' OR '.join(f'"{s}"' for s in unique[:3])
        print(f'\n� 示例（生产环境，最近 1 小时）:')
        print(f"   python3 sls_query.py production "
              f'"$(date -d -1hour +\"%Y-%m-%d %H:%M:%S\")" '
              f'"$(date +\"%Y-%m-%d %H:%M:%S\")" \'{combined}\'')
    else:
        print(f'� 日志语句中未提取到字符串常量，建议直接用关键词查询:')
        print(f'   python3 sls_query.py production <start> <end> "{feature}"')


# ─── 模式一：SLS 查询（底层调 get_logs.py）─────────────────────
def cmd_query(env, start_time, end_time, raw_query, out_path,
              envs, service_filter, get_logs_script):
    """调用 get_logs.py 执行 SLS 查询"""
    if env not in envs:
        print(f'❌ 未知环境: {env!r}')
        print(f'   可用环境: {", ".join(sorted(set(envs.keys())))}')
        sys.exit(1)
    if not _validate_time(start_time):
        print(f'❌ 开始时间格式错误: {start_time!r}（需 yyyy-MM-dd HH:mm:ss）')
        sys.exit(1)
    if not _validate_time(end_time):
        print(f'❌ 结束时间格式错误: {end_time!r}（需 yyyy-MM-dd HH:mm:ss）')
        sys.exit(1)
    if not os.path.exists(get_logs_script):
        print(f'❌ 底层脚本不存在: {get_logs_script}')
        print('   请在 data/diwang.json 的 sls.get_logs_script 中配置正确路径')
        sys.exit(1)

    query, overwritten = _force_service_filter(raw_query, service_filter)
    cfg = envs[env]

    print(f'🔍 SLS 日志查询 - {cfg["description"]}')
    print(f'   项目: {cfg["project"]}')
    print(f'   日志库: {cfg["logstore"]}')
    print(f'   时间范围: {start_time} 到 {end_time}')
    print(f'   查询语句: {query}')
    if overwritten:
        print(f'   ⚠️  已强制覆盖: 你的查询包含 service:，最终仍限定为 {service_filter}')
    else:
        print(f'   ✅  已强制追加: {service_filter}')
    if out_path:
        print(f'   输出落盘: {out_path}')
    print('-' * 60)

    cmd = [
        'python3', get_logs_script,
        cfg['project'], cfg['logstore'],
        start_time, end_time, query,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        combined = result.stdout or ''
        if result.stderr:
            combined += '\n[stderr]\n' + result.stderr

        if out_path:
            os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(combined)
            print('查询完成：完整输出已保存到文件。')
            print(_truncate(result.stdout or '', 2000))
            return

        print('查询结果（可能已截断）:')
        print(_truncate(combined, _MAX_PRINT_CHARS))
        if len(combined) > _MAX_PRINT_CHARS:
            print('提示：输出较长，建议使用 --out <文件路径> 保存完整日志。')

    except subprocess.CalledProcessError as e:
        err = (e.stdout or '')
        if e.stderr:
            err += '\n[stderr]\n' + e.stderr
        if out_path:
            os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(err)
            print(f'查询失败（错误码: {e.returncode}）。完整错误已保存到: {out_path}')
            print(_truncate(err, 2000))
        else:
            print(f'查询失败，错误码: {e.returncode}')
            print(_truncate(err, _MAX_PRINT_CHARS))
        sys.exit(1)

    except FileNotFoundError:
        print('❌ python3 命令未找到')
        sys.exit(1)

    except Exception as e:
        print(f'❌ 未知错误: {e}')
        sys.exit(1)


# ─── 入口 ─────────────────────────────────────────────────────
def main():
    envs, service_filter, get_logs_script, project_dir = _load_sls_settings()

    # analyze-logs 子命令：python3 sls_query.py analyze-logs <feature> [--project-dir <p>]
    if len(sys.argv) >= 2 and sys.argv[1] == 'analyze-logs':
        feature    = sys.argv[2] if len(sys.argv) >= 3 else ''
        custom_dir = ''
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == '--project-dir' and i + 1 < len(sys.argv):
                custom_dir = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        if not feature:
            print('用法: python3 sls_query.py analyze-logs <功能关键词> [--project-dir <路径>]')
            sys.exit(1)
        cmd_analyze_logs(feature, custom_dir or project_dir)
        return

    # 模式一：python3 sls_query.py <env> <start> <end> <query> [--out <path>]
    if len(sys.argv) not in (5, 7):
        print('❌ 参数数量不正确')
        _print_usage(envs, service_filter)
        sys.exit(1)

    env        = sys.argv[1].lower()
    start_time = sys.argv[2]
    end_time   = sys.argv[3]
    raw_query  = sys.argv[4]
    out_path   = None

    if len(sys.argv) == 7:
        if sys.argv[5] != '--out':
            print('❌ 仅支持可选参数 --out <文件路径>')
            _print_usage(envs, service_filter)
            sys.exit(1)
        out_path = sys.argv[6]

    cmd_query(env, start_time, end_time, raw_query, out_path,
              envs, service_filter, get_logs_script)


if __name__ == '__main__':
    main()
