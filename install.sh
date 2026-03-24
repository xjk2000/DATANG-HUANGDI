#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
# ⚔️ 帝王系统 · Claw DiWang · 一键安装脚本
# 中书取旨，门下封驳，尚书奉而行之
# ══════════════════════════════════════════════════════════════
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OC_HOME="$HOME/.openclaw"
OC_CFG="$OC_HOME/openclaw.json"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

banner() {
  echo ""
  echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║  ⚔️  帝王系统 · Claw DiWang                 ║${NC}"
  echo -e "${CYAN}║  中书取旨 · 门下封驳 · 尚书奉而行之           ║${NC}"
  echo -e "${CYAN}║  三省六部五监 · 17 Agent 安装向导             ║${NC}"
  echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
  echo ""
}

log()   { echo -e "${GREEN}✅ $1${NC}"; }
warn()  { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }
info()  { echo -e "${BLUE}ℹ️  $1${NC}"; }

# ── Step 0: 依赖检查 ──────────────────────────────────────────
check_deps() {
  info "检查依赖..."

  if ! command -v openclaw &>/dev/null; then
    error "未找到 openclaw CLI。请先安装 OpenClaw: https://openclaw.ai"
    exit 1
  fi
  log "OpenClaw CLI: $(openclaw --version 2>/dev/null || echo 'OK')"

  if ! command -v python3 &>/dev/null; then
    error "未找到 python3"
    exit 1
  fi
  log "Python3: $(python3 --version)"

  if [ ! -f "$OC_CFG" ]; then
    error "未找到 openclaw.json。请先运行 openclaw 完成初始化。"
    exit 1
  fi
  log "openclaw.json: $OC_CFG"
}

# ── Step 0.5: 备份已有数据 ────────────────────────────────────
backup_existing() {
  BACKUP_DIR="$OC_HOME/backups/diwang-pre-install-$(date +%Y%m%d-%H%M%S)"
  HAS_EXISTING=false

  for d in "$OC_HOME"/workspace-*/; do
    if [ -d "$d" ]; then
      HAS_EXISTING=true
      break
    fi
  done

  if $HAS_EXISTING; then
    info "检测到已有 Agent Workspace，自动备份中..."
    mkdir -p "$BACKUP_DIR"

    for d in "$OC_HOME"/workspace-*/; do
      if [ -d "$d" ]; then
        ws_name=$(basename "$d")
        cp -R "$d" "$BACKUP_DIR/$ws_name" 2>/dev/null || true
      fi
    done

    cp "$OC_CFG" "$BACKUP_DIR/openclaw.json" 2>/dev/null || true
    log "已备份到: $BACKUP_DIR"
  fi

  # 备份配置
  cp "$OC_CFG" "$OC_CFG.bak.diwang-$(date +%Y%m%d-%H%M%S)"
  log "已备份配置: $OC_CFG.bak.*"
}

# ── Step 1: 创建 Workspace ──────────────────────────────────
create_workspaces() {
  info "创建 17 个 Agent Workspace..."

  AGENTS=(
    zhongshuling zhongshu_sheren
    shizhong jishizhong
    shangshuling
    libu hubu libu_protocol bingbu xingbu gongbu
    jiangzuo shaofu junqi dushui sinong
  )

  for agent in "${AGENTS[@]}"; do
    ws="$OC_HOME/workspace-$agent"
    mkdir -p "$ws/skills"

    # 部署 SOUL.md（模板变量替换）
    if [ -f "$REPO_DIR/agents/$agent/SOUL.md" ]; then
      if [ -f "$ws/SOUL.md" ]; then
        cp "$ws/SOUL.md" "$ws/SOUL.md.bak.$(date +%Y%m%d-%H%M%S)"
      fi
      sed "s|__REPO_DIR__|$REPO_DIR|g" "$REPO_DIR/agents/$agent/SOUL.md" > "$ws/SOUL.md"
    fi

    # 部署 AGENTS.md（只在不存在时创建，避免覆盖定制版本）
    if [ -f "$REPO_DIR/agents/$agent/AGENTS.md" ]; then
      # 如果项目中有定制的 AGENTS.md，使用它
      if [ ! -f "$ws/AGENTS.md" ] || [ "$REPO_DIR/agents/$agent/AGENTS.md" -nt "$ws/AGENTS.md" ]; then
        cp "$REPO_DIR/agents/$agent/AGENTS.md" "$ws/AGENTS.md"
      fi
    elif [ ! -f "$ws/AGENTS.md" ]; then
      # 否则创建通用版本（仅在不存在时）
      cat > "$ws/AGENTS.md" << 'AGENTS_EOF'
# AGENTS.md · 帝王系统工作协议

1. 接到派令先回复「已接令」或「臣xxx已接旨」。
2. 输出必须包含：任务ID、执行结果、证据/文件路径、阻塞项。
3. 需要协作时，回复尚书令请求转派，不跨部直连。
4. 涉及删除/外发/修改生产数据等高危动作必须明确标注并等待批准。
5. 每完成一个关键步骤，用看板命令上报进展。
6. 严禁篡改其他 Agent 的 workspace 文件。
7. 严禁在未授权的情况下联系权限矩阵之外的 Agent。
AGENTS_EOF
    fi

    # 部署其他配置文件（TOOLS.md、IDENTITY.md、MEMORY.md、USER.md、HEARTBEAT.md）
    for config_file in TOOLS.md IDENTITY.md MEMORY.md USER.md HEARTBEAT.md; do
      if [ -f "$REPO_DIR/agents/$agent/$config_file" ]; then
        if [ ! -f "$ws/$config_file" ] || [ "$REPO_DIR/agents/$agent/$config_file" -nt "$ws/$config_file" ]; then
          cp "$REPO_DIR/agents/$agent/$config_file" "$ws/$config_file"
        fi
      fi
    done

    log "Workspace: $ws"
  done
}

# ── Step 2: 注册 Agents + 权限矩阵 ─────────────────────────
register_agents() {
  info "注册 17 个 Agent 并配置权限矩阵..."

  python3 << 'PYEOF'
import json, pathlib, sys

cfg_path = pathlib.Path.home() / '.openclaw' / 'openclaw.json'
cfg = json.loads(cfg_path.read_text())

# ─── Agent 定义 + subagents 权限矩阵 ───
# 权限原则：中书令→中书舍人+侍中, 侍中→给事中+尚书令, 尚书令→六部+五监, 六部/五监→尚书令
AGENTS = [
    # 三省
    {"id": "zhongshuling",    "subagents": {"allowAgents": ["zhongshu_sheren", "shizhong"]}},
    {"id": "zhongshu_sheren", "subagents": {"allowAgents": ["zhongshuling"]}},
    {"id": "shizhong",        "subagents": {"allowAgents": ["jishizhong", "shangshuling", "zhongshuling"]}},
    {"id": "jishizhong",      "subagents": {"allowAgents": ["shizhong"]}},
    {"id": "shangshuling",    "subagents": {"allowAgents": [
        "zhongshuling", "shizhong",
        "libu", "hubu", "libu_protocol", "bingbu", "xingbu", "gongbu",
        "jiangzuo", "shaofu", "junqi", "dushui", "sinong"
    ]}},
    # 六部
    {"id": "libu",            "subagents": {"allowAgents": ["shangshuling"]}},
    {"id": "hubu",            "subagents": {"allowAgents": ["shangshuling"]}},
    {"id": "libu_protocol",   "subagents": {"allowAgents": ["shangshuling"]}},
    {"id": "bingbu",          "subagents": {"allowAgents": ["shangshuling"]}},
    {"id": "xingbu",          "subagents": {"allowAgents": ["shangshuling"]}},
    {"id": "gongbu",          "subagents": {"allowAgents": ["shangshuling"]}},
    # 五监
    {"id": "jiangzuo",        "subagents": {"allowAgents": ["shangshuling"]}},
    {"id": "shaofu",          "subagents": {"allowAgents": ["shangshuling"]}},
    {"id": "junqi",           "subagents": {"allowAgents": ["shangshuling"]}},
    {"id": "dushui",          "subagents": {"allowAgents": ["shangshuling"]}},
    {"id": "sinong",          "subagents": {"allowAgents": ["shangshuling"]}},
]

agents_cfg = cfg.setdefault('agents', {})
agents_list = agents_cfg.get('list', [])
existing_ids = {a['id'] for a in agents_list}

added = 0
updated = 0
for ag in AGENTS:
    ag_id = ag['id']
    ws = str(pathlib.Path.home() / f'.openclaw/workspace-{ag_id}')

    if ag_id not in existing_ids:
        entry = {'id': ag_id, 'workspace': ws}
        # 合并 subagents
        if 'subagents' in ag:
            entry['subagents'] = ag['subagents']
        agents_list.append(entry)
        added += 1
        print(f'  + 新增: {ag_id}')
    else:
        # 更新已有 Agent 的 subagents 权限
        for existing in agents_list:
            if existing['id'] == ag_id:
                existing['workspace'] = ws
                if 'subagents' in ag:
                    existing['subagents'] = ag['subagents']
                updated += 1
                print(f'  ~ 更新: {ag_id}')
                break

agents_cfg['list'] = agents_list

# 清理 bindings 中的非法字段
bindings = cfg.get('bindings', [])
cleaned = 0
for b in bindings:
    match = b.get('match', {})
    if isinstance(match, dict) and 'pattern' in match:
        del match['pattern']
        cleaned += 1

cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
print(f'\n完成: {added} 新增, {updated} 更新, {cleaned} bindings 清理')
PYEOF

  log "Agent 注册完成"
}

# ── Step 3: 初始化数据目录 ─────────────────────────────────
init_data() {
  info "初始化数据目录..."

  mkdir -p "$REPO_DIR/data"
  mkdir -p "$REPO_DIR/data/inbox"
  mkdir -p "$REPO_DIR/data/conversations"

  # 初始化空文件
  for f in live_status.json agent_config.json dashboard_summary.json; do
    if [ ! -f "$REPO_DIR/data/$f" ]; then
      echo '{}' > "$REPO_DIR/data/$f"
    fi
  done

  # 初始任务文件
  if [ ! -f "$REPO_DIR/data/tasks_source.json" ]; then
    REPO_DIR="$REPO_DIR" python3 << 'PYEOF'
import json, pathlib, os
from datetime import datetime, timezone

now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
tasks = [
    {
        "id": "CL-INIT-001",
        "title": "帝王系统初始化完成",
        "official": "工部尚书",
        "org": "工部",
        "state": "Done",
        "now": "三省六部五监系统已就绪",
        "eta": "-",
        "block": "无",
        "output": "17 Agent 全部注册，权限矩阵配置完毕",
        "ac": "系统正常运行",
        "progress": "",
        "plan": "",
        "todos": [],
        "flow_log": [
            {"at": now, "from": "皇上", "to": "中书省", "remark": "下旨初始化帝王系统"},
            {"at": now, "from": "中书省", "to": "门下省", "remark": "初始化方案提交审核"},
            {"at": now, "from": "门下省", "to": "尚书省", "remark": "✅ 准奏"},
            {"at": now, "from": "尚书省", "to": "工部", "remark": "派发：系统初始化"},
            {"at": now, "from": "工部", "to": "皇上", "remark": "✅ 回奏：初始化完成"},
        ],
        "created_at": now,
        "updated_at": now,
    }
]
data_dir = pathlib.Path(os.environ.get('REPO_DIR', '.')) / 'data'
data_dir.mkdir(exist_ok=True)
(data_dir / 'tasks_source.json').write_text(json.dumps(tasks, ensure_ascii=False, indent=2))
print('tasks_source.json 已初始化')
PYEOF
  fi

  # 初始化飞书渠道配置
  if [ ! -f "$REPO_DIR/data/feishu_channels.json" ]; then
    echo '{}' > "$REPO_DIR/data/feishu_channels.json"
  fi

  log "数据目录初始化完成: $REPO_DIR/data"
}

# ── Step 3.5: 创建 data/scripts 软链接 ────────────────────
link_resources() {
  info "创建 data/scripts 软链接以确保 Agent 数据一致..."

  AGENTS=(
    zhongshuling zhongshu_sheren
    shizhong jishizhong
    shangshuling
    libu hubu libu_protocol bingbu xingbu gongbu
    jiangzuo shaofu junqi dushui sinong
  )

  LINKED=0
  for agent in "${AGENTS[@]}"; do
    ws="$OC_HOME/workspace-$agent"
    mkdir -p "$ws"

    # 软链接 data 目录
    ws_data="$ws/data"
    if [ -L "$ws_data" ]; then
      : # 已是软链接
    elif [ -d "$ws_data" ]; then
      mv "$ws_data" "${ws_data}.bak.$(date +%Y%m%d-%H%M%S)"
      ln -s "$REPO_DIR/data" "$ws_data"
      LINKED=$((LINKED + 1))
    else
      ln -s "$REPO_DIR/data" "$ws_data"
      LINKED=$((LINKED + 1))
    fi

    # 软链接 scripts 目录
    ws_scripts="$ws/scripts"
    if [ -L "$ws_scripts" ]; then
      :
    elif [ -d "$ws_scripts" ]; then
      mv "$ws_scripts" "${ws_scripts}.bak.$(date +%Y%m%d-%H%M%S)"
      ln -s "$REPO_DIR/scripts" "$ws_scripts"
      LINKED=$((LINKED + 1))
    else
      ln -s "$REPO_DIR/scripts" "$ws_scripts"
      LINKED=$((LINKED + 1))
    fi
  done

  log "已创建 $LINKED 个软链接（data/scripts → 项目目录）"
}

# ── Step 3.6: 设置 Agent 间通信可见性 ────────────────────
setup_visibility() {
  info "配置 Agent 间消息可见性..."
  if openclaw config set tools.sessions.visibility all 2>/dev/null; then
    log "已设置 tools.sessions.visibility=all（Agent 间可互相通信）"
  else
    warn "设置 visibility 失败（可能 openclaw 版本不支持），请手动执行:"
    echo "    openclaw config set tools.sessions.visibility all"
  fi
}

# ── Step 3.7: 同步 API Key 到所有 Agent ──────────────────
sync_auth() {
  info "同步 API Key 到所有 Agent..."

  MAIN_AUTH="$OC_HOME/agents/main/agent/auth-profiles.json"
  if [ ! -f "$MAIN_AUTH" ]; then
    MAIN_AUTH=$(find "$OC_HOME/agents" -name auth-profiles.json -maxdepth 3 2>/dev/null | head -1)
  fi

  if [ -z "$MAIN_AUTH" ] || [ ! -f "$MAIN_AUTH" ]; then
    warn "未找到已有的 auth-profiles.json"
    warn "请先为任意 Agent 配置 API Key，然后重新运行 install.sh"
    return
  fi

  if ! python3 -c "import json; d=json.load(open('$MAIN_AUTH')); assert d" 2>/dev/null; then
    warn "auth-profiles.json 为空或无效，请先配置 API Key"
    return
  fi

  AGENTS=(
    zhongshuling zhongshu_sheren
    shizhong jishizhong
    shangshuling
    libu hubu libu_protocol bingbu xingbu gongbu
    jiangzuo shaofu junqi dushui sinong
  )

  SYNCED=0
  for agent in "${AGENTS[@]}"; do
    AGENT_DIR="$OC_HOME/agents/$agent/agent"
    if [ -d "$AGENT_DIR" ] || mkdir -p "$AGENT_DIR" 2>/dev/null; then
      cp "$MAIN_AUTH" "$AGENT_DIR/auth-profiles.json"
      SYNCED=$((SYNCED + 1))
    fi
  done

  log "API Key 已同步到 $SYNCED 个 Agent"
  info "来源: $MAIN_AUTH"
}

# ── Step 4: 首次数据同步 ──────────────────────────────────
first_sync() {
  info "执行首次数据同步..."
  cd "$REPO_DIR"

  REPO_DIR="$REPO_DIR" python3 scripts/sync_from_openclaw.py || warn "sync_from_openclaw 有警告"
  python3 scripts/refresh_live_data.py || warn "refresh_live_data 有警告"

  log "首次同步完成"
}

# ── Step 5: 重启 Gateway ──────────────────────────────────
restart_gateway() {
  info "重启 OpenClaw Gateway..."
  if openclaw gateway restart 2>/dev/null; then
    log "Gateway 重启成功"
  else
    warn "Gateway 重启失败，请手动重启：openclaw gateway restart"
  fi
}

# ── Step 6: 启动 Dashboard 服务器 ──────────────────────────
start_dashboard() {
  info "启动 Dashboard 服务器..."

  # 先停止旧的 Dashboard 进程（确保使用最新版本）
  if pgrep -f "python3.*dashboard/server.py" > /dev/null; then
    warn "检测到旧的 Dashboard，正在停止..."
    pkill -f "python3.*dashboard/server.py" || true
    sleep 2
  fi

  # 后台启动
  cd "$REPO_DIR"
  nohup python3 dashboard/server.py > "$REPO_DIR/data/dashboard.log" 2>&1 &
  DASHBOARD_PID=$!
  sleep 2

  # 验证启动
  if ps -p $DASHBOARD_PID > /dev/null 2>&1; then
    log "Dashboard 已启动 (PID: $DASHBOARD_PID)"
    log "访问地址: http://127.0.0.1:7891"
  else
    warn "Dashboard 启动失败，请查看日志: $REPO_DIR/data/dashboard.log"
  fi
}

# ── Step 6.5: 启动朝堂 WebSocket 服务器 ──────────────────
start_court_server() {
  info "启动朝堂 WebSocket 服务器..."

  # 先停止旧的服务器进程（确保使用最新版本）
  if pgrep -f "python3.*session/server.py" > /dev/null; then
    warn "检测到旧的朝堂服务器，正在停止..."
    pkill -f "python3.*session/server.py" || true
    sleep 2
  fi

  # 检查 websockets 模块
  if ! python3 -c "import websockets" 2>/dev/null; then
    warn "未安装 websockets 模块，正在安装..."
    pip3 install websockets --quiet || {
      warn "websockets 安装失败，请手动安装: pip3 install websockets"
      return
    }
  fi

  # 后台启动
  cd "$REPO_DIR"
  nohup python3 scripts/session/server.py > "$REPO_DIR/data/court_server.log" 2>&1 &
  COURT_PID=$!
  sleep 2

  # 验证启动
  if ps -p $COURT_PID > /dev/null 2>&1; then
    log "朝堂服务器已启动 (PID: $COURT_PID)"
    log "WebSocket: ws://127.0.0.1:7893"
    log "Web 界面: http://127.0.0.1:7891/court.html"
  else
    warn "朝堂服务器启动失败，请查看日志: $REPO_DIR/data/court_server.log"
  fi
}

# ── Step 6.6: 启动所有 Agent 朝堂监听客户端 ─────────────
start_agent_listeners() {
  info "启动所有 Agent 朝堂监听客户端..."
  
  # 调用独立的启动脚本
  if [ -f "$REPO_DIR/scripts/start_all_agents.sh" ]; then
    bash "$REPO_DIR/scripts/start_all_agents.sh"
  else
    warn "未找到 scripts/start_all_agents.sh，跳过 Agent 监听启动"
  fi
}

# ── Step 7: 创建 .gitignore ──────────────────────────────
create_gitignore() {
  if [ ! -f "$REPO_DIR/.gitignore" ]; then
    cat > "$REPO_DIR/.gitignore" << 'EOF'
data/
*.pyc
__pycache__/
.DS_Store
*.tmp-*
*.bak.*
node_modules/
dist/
*.log
EOF
    log ".gitignore 已创建"
  fi
}

# ── Main ──────────────────────────────────────────────────
banner
check_deps
backup_existing
create_workspaces
register_agents
init_data
link_resources
setup_visibility
sync_auth
first_sync
restart_gateway
start_dashboard
start_court_server
start_agent_listeners
create_gitignore

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉  帝王系统安装完成！17 Agent 已就位！             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo "三省："
echo "  📜 中书令 (zhongshuling)     - 取旨起草"
echo "  📝 中书舍人 (zhongshu_sheren) - 记录辅析"
echo "  🔍 侍中侍郎 (shizhong)      - 审查决策"
echo "  ⚖️  给事中 (jishizhong)      - 排查驳正"
echo "  📮 尚书令 (shangshuling)     - 派发协调"
echo ""
echo "六部："
echo "  👥 吏部 (libu)          - HR & Lifecycle"
echo "  💰 户部 (hubu)          - Data & Biz"
echo "  📋 礼部 (libu_protocol) - API & Standard"
echo "  ⚔️  兵部 (bingbu)        - SRE & Infra"
echo "  🔒 刑部 (xingbu)        - QA & Audit"
echo "  🔧 工部 (gongbu)        - Platform & Base"
echo ""
echo "五监："
echo "  🏗️  将作监 (jiangzuo) - 核心业务开发"
echo "  🎨 少府监 (shaofu)   - 前端与交互"
echo "  🛡️  军器监 (junqi)    - 安全工具"
echo "  🌊 都水监 (dushui)   - 流计算"
echo "  🌾 司农监 (sinong)   - 算法与数据"
echo ""
echo "下一步："
echo "  1. 启动数据刷新:   bash scripts/run_loop.sh &"
echo "  2. 打开看板:       open http://127.0.0.1:7891"
echo "  3. 进入朝堂:       open http://127.0.0.1:7891/court.html"
echo "  4. 配置飞书渠道:   http://127.0.0.1:7891/channels.html"
echo ""
echo "朝堂会话室（实时群聊）："
echo "  ✅ 朝堂服务器已启动:  ws://127.0.0.1:7893"
echo "  ✅ 所有 Agent 已自动进入朝堂监听"
echo "  📋 Web 界面:  http://127.0.0.1:7891/court.html"
echo "  📂 Agent 日志: data/agent_listeners/<agent_id>.log"
echo ""
echo "使用方式："
echo "  1. 打开 Web 界面，在朝堂中下旨"
echo "  2. Agent 收到 to:自己 的消息后自动接旨并调用 OpenClaw"
echo "  3. 查看 Agent 日志: tail -f data/agent_listeners/zhongshuling.log"
echo ""
echo "管理命令："
echo "  启动所有 Agent:    bash scripts/start_all_agents.sh"
echo "  查看所有监听进程:  pgrep -af agent_client.py"
echo "  停止所有监听:      pkill -f agent_client.py"
echo "  重启单个 Agent:    pkill -f 'agent_client.py zhongshuling' && \\"
echo "                     nohup python3 scripts/session/agent_client.py zhongshuling > data/agent_listeners/zhongshuling.log 2>&1 &"
echo ""
warn "如 API Key 未同步，请运行: ./install.sh"
info "文档: README.md"
