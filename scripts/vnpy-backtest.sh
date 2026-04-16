#!/bin/bash
# VNPy策略回测脚本
#
# 用法:
#   bash ~/.codeflicker/skills/stock-screener/scripts/vnpy-backtest.sh
#   bash ~/.codeflicker/skills/stock-screener/scripts/vnpy-backtest.sh --days 5 --max 10
#

echo "================================"
echo " VNPy策略回测引擎"
echo "================================"
echo ""

# 默认参数
DAYS=5
MAX_STOCKS=""
FILE=""

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --days)
            DAYS="$2"
            shift 2
            ;;
        --max)
            MAX_STOCKS="--max $2"
            shift 2
            ;;
        --file)
            FILE="--file $2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# 运行回测
echo ">>> 持仓天数: $DAYS 天"
echo ""

if [ -n "$FILE" ]; then
    python3 ~/vnpy_backtest_signals.py --days $DAYS $MAX_STOCKS $FILE
else
    python3 ~/vnpy_backtest_signals.py --days $DAYS $MAX_STOCKS
fi

echo ""
echo ">>> 回测完成！"
