#!/usr/bin/env bash
# ─── 帝王系统 · 数据刷新循环 ──────────────────────────────
# 每 15 秒刷新一次运行时数据
# 用法: bash scripts/run_loop.sh

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export REPO_DIR

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ⚔️  帝王系统 · 数据刷新循环      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}数据目录: $REPO_DIR/data${NC}"
echo -e "${GREEN}刷新间隔: 15 秒${NC}"
echo ""

CYCLE=0
while true; do
    CYCLE=$((CYCLE + 1))
    TS=$(date '+%H:%M:%S')

    # 同步 OpenClaw 运行时数据
    python3 "$REPO_DIR/scripts/sync_from_openclaw.py" 2>/dev/null || true

    # 同步 OpenClaw 会话到看板
    if [ -f "$REPO_DIR/scripts/sync_sessions_to_kanban.py" ]; then
        python3 "$REPO_DIR/scripts/sync_sessions_to_kanban.py" 2>/dev/null || true
    fi

    # 刷新看板实时数据
    if [ -f "$REPO_DIR/scripts/refresh_live_data.py" ]; then
        python3 "$REPO_DIR/scripts/refresh_live_data.py" 2>/dev/null || true
    fi

    echo -e "${BLUE}[$TS] 周期 #$CYCLE 完成${NC}"
    sleep 15
done
