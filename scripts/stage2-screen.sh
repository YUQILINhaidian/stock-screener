#!/bin/bash
#
# 第二阶段选股策略
# 根据 Mark Minervini 的8条标准筛选处于第二阶段的股票
#
# 使用方法:
#   ./stage2-screen.sh
#   ./stage2-screen.sh --min-low-ratio 1.3
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Python脚本路径
PYTHON_SCRIPT="$HOME/screen_stage2.py"

# 数据库路径
DB_PATH="$HOME/.vntrader/database.db"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   第二阶段选股策略${NC}"
echo -e "${BLUE}   《股票魔法师》Mark Minervini${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查Python脚本是否存在
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo -e "${RED}错误: Python脚本不存在: $PYTHON_SCRIPT${NC}"
    exit 1
fi

# 检查数据库是否存在
if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}错误: 数据库不存在: $DB_PATH${NC}"
    exit 1
fi

# 检查数据新鲜度
echo -e "${YELLOW}检查数据新鲜度...${NC}"
LATEST_DATE=$(sqlite3 "$DB_PATH" "SELECT MAX(datetime) FROM dbbardata WHERE interval='d'" 2>/dev/null)
echo "数据库最新日期: $LATEST_DATE"

# 执行筛选
echo ""
echo -e "${GREEN}开始执行筛选...${NC}"
echo "筛选标准: Mark Minervini 8条标准"
echo ""

python3 "$PYTHON_SCRIPT" "$@"

echo ""
echo -e "${GREEN}筛选完成!${NC}"
echo ""
echo -e "${YELLOW}提示:${NC}"
echo "  1. 筛选结果已保存到 ~/.vntrader/screen_results/ 目录"
echo "  2. 重点关注位置接近100%的股票"
echo "  3. 建议结合K线图和成交量分析"
echo "  4. 可使用 --min-low-ratio 1.3 调整筛选严格度"
echo ""
