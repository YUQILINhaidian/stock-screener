#!/bin/bash
#
# 接近一年新高选股策略
# 根据陶博士2006的方法：CLOSE/HHV(HIGH,250) > 0.9
#
# 使用方法:
#   ./near-year-high.sh
#   ./near-year-high.sh --threshold 0.95
#   ./near-year-high.sh --output results.csv
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Python脚本路径
PYTHON_SCRIPT="$HOME/screen_near_year_high.py"

# 默认参数
THRESHOLD=${1:-0.9}
OUTPUT=${2:-}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   接近一年新高选股策略${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查Python脚本是否存在
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo -e "${RED}错误: Python脚本不存在: $PYTHON_SCRIPT${NC}"
    echo "请先运行: python3 ~/screen_near_year_high.py"
    exit 1
fi

# 检查数据库是否存在
DB_PATH="$HOME/.vntrader/database.db"
if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}错误: 数据库不存在: $DB_PATH${NC}"
    echo "请先更新数据"
    exit 1
fi

# 检查数据新鲜度
echo -e "${YELLOW}检查数据新鲜度...${NC}"
LATEST_DATE=$(sqlite3 "$DB_PATH" "SELECT MAX(datetime) FROM dbbardata WHERE interval='d'" 2>/dev/null)
echo "数据库最新日期: $LATEST_DATE"

# 执行筛选
echo ""
echo -e "${GREEN}开始执行筛选...${NC}"
echo "筛选阈值: $THRESHOLD (即位置 >= $(echo "$THRESHOLD * 100" | bc)%)"
echo ""

if [ -n "$OUTPUT" ]; then
    python3 "$PYTHON_SCRIPT" --threshold "$THRESHOLD" --output "$OUTPUT"
else
    python3 "$PYTHON_SCRIPT" --threshold "$THRESHOLD"
fi

echo ""
echo -e "${GREEN}筛选完成!${NC}"
echo ""
echo -e "${YELLOW}提示:${NC}"
echo "  1. 筛选结果已保存到 ~/.vntrader/screen_results/ 目录"
echo "  2. 建议结合K线图逐个分析筛选结果"
echo "  3. 特别关注创一年新高(标记★)的股票"
echo "  4. 可使用 --threshold 0.95 调整筛选严格度"
echo ""
