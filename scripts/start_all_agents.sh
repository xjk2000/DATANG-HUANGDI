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

started=0
skipped=0

for agent in "${AGENTS[@]}"; do
  # 检查是否已在运行
  if pgrep -f "agent_client.py $agent" > /dev/null 2>&1; then
    echo -e "  ${YELLOW}⊙${NC} $agent (已在运行)"
    skipped=$((skipped + 1))
    continue
  fi

  # 后台启动
  nohup python3 "$SCRIPT_DIR/session/agent_client.py" "$agent" \
    > "$LOG_DIR/$agent.log" 2>&1 &
  
  echo -e "  ${GREEN}✓${NC} $agent (已启动)"
  started=$((started + 1))
done

echo ""
echo -e "${GREEN}完成！${NC}"
echo "  启动: $started 个"
echo "  跳过: $skipped 个"
echo ""
echo "查看日志："
echo "  tail -f $LOG_DIR/zhongshuling.log"
echo ""
echo "管理命令："
echo "  查看所有进程: pgrep -af agent_client.py"
echo "  停止所有监听: pkill -f agent_client.py"
echo ""
