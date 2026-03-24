#!/bin/bash
#
# 启动所有 Agent 朝堂监听客户端
#

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

# 路径
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_DIR=$(dirname "$SCRIPT_DIR")
DATA_DIR="$REPO_DIR/data"
LOG_DIR="$DATA_DIR/agent_listeners"

# 创建日志目录
mkdir -p "$LOG_DIR"

# Agent 列表
AGENTS=(
  zhongshuling zhongshu_sheren
  shizhong jishizhong
  shangshuling
  libu hubu libu_protocol bingbu xingbu gongbu
  jiangzuo shaofu junqi dushui sinong
)

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🏛️  启动所有 Agent 朝堂监听          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

# 先停止所有旧的 Agent 监听进程（确保干净的初始化）
if pgrep -f "agent_client.py" > /dev/null 2>&1; then
  echo -e "${YELLOW}检测到旧的 Agent 监听进程，正在停止...${NC}"
  pkill -f "agent_client.py" || true
  sleep 2
  echo ""
fi

started=0

for agent in "${AGENTS[@]}"; do
  # 创建或更新启动标记文件
  echo "started at $(date '+%Y-%m-%d %H:%M:%S')" > "$LOG_DIR/$agent.start"

  # 后台启动
  nohup python3 "$SCRIPT_DIR/session/agent_client.py" "$agent" \
    > "$LOG_DIR/$agent.log" 2>&1 &
  
  echo -e "  ${GREEN}✓${NC} $agent (已启动)"
  started=$((started + 1))
done

echo ""
echo -e "${GREEN}完成！${NC}"
echo "  已启动: $started 个 Agent 监听客户端"
echo ""
echo "查看日志："
echo "  tail -f $LOG_DIR/zhongshuling.log"
echo ""
echo "管理命令："
echo "  查看所有进程: pgrep -af agent_client.py"
echo "  停止所有监听: pkill -f agent_client.py"
echo ""
